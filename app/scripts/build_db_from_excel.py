# app/scripts/build_db_from_excel.py
import os
from typing import List, Dict, Tuple
import pandas as pd
from sqlalchemy import create_engine, text

# -------- CONFIG (reads from env, with safe defaults for local dev) --------
DB_USER = os.getenv("DB_USER", "futuremed")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cost")   # << changed from DB_PASS
DB_HOST = os.getenv("DB_HOST", "mysql")          # docker service name
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "futuremed")

# New repo layout: we mount ../data -> /app/data (read-only)
EXCEL_PATH = os.getenv("EXCEL_PATH", "/app/data/master/db_ready_master_cca_tools.xlsx")
SHEET_NAME = "Inventory"

# Authoritative columns in the Excel (includes scope + new content fields)
COLS = [
    "tool_id","tool_name","user_group","sector","tool_type",
    "political_scale","physical_scale",
    "temporal_scale","temporal_resolution","methodological_approach","data_utilization",
    "output_type","accessibility_and_usability",
    "is_multi_language","language",
    "customizability","integration_capability",
    "validation_and_reliability","cost","maintenance","support",
    "primary_area_scope","primary_area_of_focus",
    "tool_description","bullet1","bullet2","bullet3",
    "link"
]

# Link tables -> source Excel columns (multi-value, comma-separated)
LINK_MAP: Dict[str, List[str]] = {
    "Tool_UserGroup": ["user_group"],
    "Tool_SectorFocus": ["sector"],
    "Tool_ToolType": ["tool_type"],
    "Tool_TargetScale_Political": ["political_scale"],
    "Tool_TargetScale_Physical": ["physical_scale"],
    "Tool_TemporalScale": ["temporal_scale"],
    "Tool_TemporalResolution": ["temporal_resolution"],
    "Tool_MethodologicalApproach": ["methodological_approach"],
    "Tool_DataUtilization": ["data_utilization"],
    "Tool_OutputType": ["output_type"],
    "Tool_AccessibilityAndUsability": ["accessibility_and_usability"],
    "Tool_Maintenance": ["maintenance"],
    "Tool_Support": ["support"],
    "Tool_Language": ["language"],
    "Tool_Area": ["primary_area_of_focus"],  # free-text names; scope lives in Tools.primary_area_scope
}

def norm(s: str) -> str:
    """Trim only. No auto-corrections so Excel remains the source of truth."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    return str(s).strip()

def split_multi(val: str) -> List[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    parts = [p.strip() for p in str(val).split(",")]
    return [p for p in parts if p]

def load_excel(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel not found at: {path}")
    print(f"📄 Reading: {path} (sheet={SHEET_NAME})")
    df = pd.read_excel(path, sheet_name=SHEET_NAME, engine="openpyxl")

    missing = [c for c in COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in Excel: {missing}")

    df = df[COLS].copy()

    # Normalize strings (trim only)
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(norm)

    # tool_id to int (strict)
    df["tool_id"] = pd.to_numeric(df["tool_id"], errors="raise")
    return df

def make_engine():
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url, pool_pre_ping=True)

def drop_and_create_schema(engine):
    with engine.begin() as con:
        print("🧹 Dropping old tables (if any)…")
        con.execute(text("SET FOREIGN_KEY_CHECKS=0;"))
        con.execute(text("""
            DROP TABLE IF EXISTS
              Tool_Area, Tool_Language, Tool_Support, Tool_Maintenance,
              Tool_AccessibilityAndUsability, Tool_OutputType, Tool_DataUtilization,
              Tool_MethodologicalApproach, Tool_TemporalResolution, Tool_TemporalScale,
              Tool_TargetScale_Physical, Tool_TargetScale_Political, Tool_ToolType,
              Tool_SectorFocus, Tool_UserGroup, Tools;
        """))
        con.execute(text("SET FOREIGN_KEY_CHECKS=1;"))

        print("🏗️  Creating schema…")
        con.execute(text(f"""
        CREATE TABLE Tools (
          tool_id INT PRIMARY KEY,
          tool_name VARCHAR(255) NOT NULL,
          is_multi_language VARCHAR(10),
          customizability VARCHAR(50),
          integration_capability VARCHAR(50),
          validation_and_reliability VARCHAR(100),
          cost VARCHAR(100),
          maintenance VARCHAR(100),
          support VARCHAR(100),
          primary_area_scope VARCHAR(30),    -- Global/Continent/Region/Country/Subnational
          primary_area_of_focus TEXT,        -- original free text (kept for reference)
          tool_description MEDIUMTEXT,
          bullet1 VARCHAR(255),
          bullet2 VARCHAR(255),
          bullet3 VARCHAR(255),
          link TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          FULLTEXT KEY ft_tools_text (tool_name, tool_description, bullet1, bullet2, bullet3)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """))

        def create_link(name: str):
            con.execute(text(f"""
              CREATE TABLE {name} (
                tool_id INT NOT NULL,
                label VARCHAR(255) NOT NULL,
                PRIMARY KEY (tool_id, label),
                INDEX idx_{name}_label (label),
                CONSTRAINT fk_{name}_tool FOREIGN KEY (tool_id) REFERENCES Tools(tool_id) ON DELETE CASCADE
              ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))

        for t in LINK_MAP.keys():
            create_link(t)

def insert_tools(engine, df: pd.DataFrame):
    tools_cols = [
        "tool_id","tool_name","is_multi_language",
        "customizability","integration_capability",
        "validation_and_reliability","cost","maintenance","support",
        "primary_area_scope","primary_area_of_focus",
        "tool_description","bullet1","bullet2","bullet3",
        "link",
    ]
    tbl = df[tools_cols].copy()
    # Empty strings -> NULL (so filters behave sensibly)
    tbl = tbl.where(tbl.ne(""), None)
    tbl.to_sql("Tools", engine, if_exists="append", index=False)

def insert_links(engine, df: pd.DataFrame):
    def write(table: str, pairs: List[Tuple[int,str]]):
        if not pairs:
            return
        out = pd.DataFrame(pairs, columns=["tool_id","label"]).drop_duplicates()
        out.to_sql(table, engine, if_exists="append", index=False)

    for table, src_cols in LINK_MAP.items():
        pairs: List[Tuple[int,str]] = []
        for _, row in df.iterrows():
            tid = int(row["tool_id"])
            labels: List[str] = []
            for c in src_cols:
                labels += split_multi(row[c])
            for lab in labels:
                if lab:
                    pairs.append((tid, lab))
        write(table, pairs)

def create_view(engine):
    with engine.begin() as con:
        print("🔭 Creating QA view view_tools_full …")
        con.execute(text("DROP VIEW IF EXISTS view_tools_full"))
        con.execute(text("""
        CREATE VIEW view_tools_full AS
        SELECT
            t.*,
            GROUP_CONCAT(DISTINCT ug.label ORDER BY ug.label SEPARATOR ', ') AS user_group,
            GROUP_CONCAT(DISTINCT sf.label ORDER BY sf.label SEPARATOR ', ') AS sector,
            GROUP_CONCAT(DISTINCT tt.label ORDER BY tt.label SEPARATOR ', ') AS tool_type,
            GROUP_CONCAT(DISTINCT tsp.label ORDER BY tsp.label SEPARATOR ', ') AS political_scale,
            GROUP_CONCAT(DISTINCT tsph.label ORDER BY tsph.label SEPARATOR ', ') AS physical_scale,
            GROUP_CONCAT(DISTINCT ts.label ORDER BY ts.label SEPARATOR ', ') AS temporal_scale,
            GROUP_CONCAT(DISTINCT tr.label ORDER BY tr.label SEPARATOR ', ') AS temporal_resolution,
            GROUP_CONCAT(DISTINCT ma.label ORDER BY ma.label SEPARATOR ', ') AS methodological_approach,
            GROUP_CONCAT(DISTINCT du.label ORDER BY du.label SEPARATOR ', ') AS data_utilization,
            GROUP_CONCAT(DISTINCT ot.label ORDER BY ot.label SEPARATOR ', ') AS output_type,
            GROUP_CONCAT(DISTINCT au.label ORDER BY au.label SEPARATOR ', ') AS accessibility_and_usability,
            GROUP_CONCAT(DISTINCT m.label ORDER BY m.label SEPARATOR ', ') AS maintenance_multi,
            GROUP_CONCAT(DISTINCT s.label ORDER BY s.label SEPARATOR ', ') AS support_multi,
            GROUP_CONCAT(DISTINCT l.label ORDER BY l.label SEPARATOR ', ') AS language_multi,
            GROUP_CONCAT(DISTINCT a.label ORDER BY a.label SEPARATOR ', ') AS area_multi
        FROM Tools t
        LEFT JOIN Tool_UserGroup ug ON t.tool_id = ug.tool_id
        LEFT JOIN Tool_SectorFocus sf ON t.tool_id = sf.tool_id
        LEFT JOIN Tool_ToolType tt ON t.tool_id = tt.tool_id
        LEFT JOIN Tool_TargetScale_Political tsp ON t.tool_id = tsp.tool_id
        LEFT JOIN Tool_TargetScale_Physical tsph ON t.tool_id = tsph.tool_id
        LEFT JOIN Tool_TemporalScale ts ON t.tool_id = ts.tool_id
        LEFT JOIN Tool_TemporalResolution tr ON t.tool_id = tr.tool_id
        LEFT JOIN Tool_MethodologicalApproach ma ON t.tool_id = ma.tool_id
        LEFT JOIN Tool_DataUtilization du ON t.tool_id = du.tool_id
        LEFT JOIN Tool_OutputType ot ON t.tool_id = ot.tool_id
        LEFT JOIN Tool_AccessibilityAndUsability au ON t.tool_id = au.tool_id
        LEFT JOIN Tool_Maintenance m ON t.tool_id = m.tool_id
        LEFT JOIN Tool_Support s ON t.tool_id = s.tool_id
        LEFT JOIN Tool_Language l ON t.tool_id = l.tool_id
        LEFT JOIN Tool_Area a ON t.tool_id = a.tool_id
        GROUP BY t.tool_id;
        """))

def main():
    print("🚀 Import starting…")
    print(f"🔧 DB target: mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"📦 Excel path: {EXCEL_PATH}")

    df = load_excel(EXCEL_PATH)
    eng = make_engine()

    drop_and_create_schema(eng)
    insert_tools(eng, df)
    insert_links(eng, df)
    create_view(eng)

    print("✅ Done. Database rebuilt from Excel and view_tools_full created.")

if __name__ == "__main__":
    main()