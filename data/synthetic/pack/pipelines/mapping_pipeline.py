"""
Mapping pipeline – reloads all 8 reference / control tables in StarRocks.
Executes the SQL file that contains the full INSERT data.
"""
import os
import subprocess


_SQL_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "ddl", "starrocks", "22_mapping_data_reload.sql",
)


def reload_mapping_tables() -> bool:
    sql_path = os.path.abspath(_SQL_FILE)
    if not os.path.exists(sql_path):
        print(f"  [SKIP] Mapping SQL not found: {sql_path}")
        return False

    print(f"→ Reloading mapping tables from {os.path.basename(sql_path)} …")
    with open(sql_path, "r") as fh:
        sql = fh.read()

    cmd = [
        "docker", "exec", "-i", "dataprismai-starrocks",
        "mysql", "-h127.0.0.1", "-uroot", "-P9030", "cc_analytics",
    ]
    result = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"  [ERROR] {result.stderr[:400]}")
        return False

    print("  Mapping tables reloaded successfully.")
    return True
