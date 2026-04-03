import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Mini IronBook", layout="wide")
st.title("Mini IronBook - Data Migration Dashboard")

BACKEND_URL = "http://localhost:8000"


# --- Discovery ---
st.header("Step 1: Discovery")

if st.button("Run Discovery", type="primary"):
    with st.spinner("Scanning source database..."):
        resp = httpx.post(f"{BACKEND_URL}/api/discovery/run", timeout=30)
    if resp.status_code == 200:
        st.session_state["discovery"] = resp.json()
        st.success("Discovery complete!")
    else:
        st.error(f"Discovery failed: {resp.text}")

if "discovery" in st.session_state:
    data = st.session_state["discovery"]

    # --- Tables overview ---
    st.subheader("Tables")
    overview = []
    for t in data["tables"]:
        overview.append({
            "Table": t["name"],
            "Columns": len(t["columns"]),
            "Primary Key": ", ".join(t["primary_key"]),
            "Foreign Keys": len(t["foreign_keys"]),
            "Indexes": len(t["indexes"]),
            "Rows": t["row_count"],
        })
    st.dataframe(pd.DataFrame(overview), use_container_width=True, hide_index=True)

    # --- Table details ---
    st.subheader("Table Details")
    for t in data["tables"]:
        with st.expander(f"{t['name']} ({len(t['columns'])} columns, {t['row_count']} rows)"):
            cols_df = pd.DataFrame([
                {
                    "Column": c["name"],
                    "Type": c["data_type"],
                    "Nullable": c["nullable"],
                    "PK": c["is_primary_key"],
                    "Default": c["default"] or "",
                }
                for c in t["columns"]
            ])
            st.dataframe(cols_df, use_container_width=True, hide_index=True)

            if t["foreign_keys"]:
                st.markdown("**Foreign Keys:**")
                for fk in t["foreign_keys"]:
                    st.markdown(
                        f"- `{', '.join(fk['constrained_columns'])}` → "
                        f"`{fk['referred_table']}.{', '.join(fk['referred_columns'])}`"
                    )

    # --- Stored Procedures ---
    if data["stored_procedures"]:
        st.subheader("Stored Procedures")
        for proc in data["stored_procedures"]:
            with st.expander(f"Procedure: {proc['name']}"):
                st.code(proc["body"], language="sql")

    # --- Dependency Graph ---
    st.subheader("Dependency Graph")
    graph_resp = httpx.get(f"{BACKEND_URL}/api/discovery/graph", timeout=10)
    if graph_resp.status_code == 200:
        graph_data = graph_resp.json()
        st.graphviz_chart(graph_data["dot"])
        st.markdown(f"**Migration load order:** `{'` → `'.join(graph_data['load_order'])}`")
    else:
        st.warning("Could not load dependency graph.")
