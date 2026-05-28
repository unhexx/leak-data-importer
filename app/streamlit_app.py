"""
Leak Data Importer - Dynamic Import Control & Investigation UI

Run with:
    streamlit run app/streamlit_app.py

This is a minimalist but powerful interface for:
- Running imports with full visibility
- Seeing exactly what was extracted
- Searching entities
- Visualizing relationship graphs
"""

from __future__ import annotations

import streamlit as st
from pathlib import Path
import tempfile
import json

# Make sure we can import the package
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from leak_data_importer.importers.txt_report import TxtReportImporter
from leak_data_importer.graph.result import ImportGraphResult

st.set_page_config(page_title="Leak Importer Control", layout="wide", page_icon="🔍")

st.title("🔍 Leak Data Importer — Control Center")
st.caption("Minimalist dynamic interface for import success monitoring + investigation")

# ==================== SIDEBAR: Import Controls ====================
with st.sidebar:
    st.header("Import Control")

    source_path = st.text_input(
        "Source path (file or folder)",
        value=r"X:\LocalRepo\leak-data-importer\data\raw",
        help="Path to report_*.txt files or a single file"
    )

    run_import = st.button("🚀 Run Import", type="primary", use_container_width=True)

    st.divider()
    st.markdown("**Options**")
    show_raw = st.checkbox("Attach all raw fields (lossless)", value=True)

# ==================== MAIN: Import Execution & Stats ====================
if run_import:
    source = Path(source_path)
    if not source.exists():
        st.error(f"Path does not exist: {source}")
        st.stop()

    with st.spinner("Importing..."):
        importer = TxtReportImporter(source)
        result: ImportGraphResult = importer.parse_to_graph()

    st.session_state["last_result"] = result
    st.session_state["last_source"] = str(source)

    st.success(f"Import completed successfully")

# Show last result if available
result = st.session_state.get("last_result")

if result:
    st.subheader("📊 Import Success Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    s = result.summary()

    col1.metric("Entities", s["entities_total"])
    col2.metric("Relationships", s["relationships_total"])
    col3.metric("Flat Records", s["flat_records"])
    col4.metric("Low Confidence", result.stats.get("parser_stats", {}).get("low_confidence_records", 0))

    # Entity breakdown
    st.markdown("### Entities by Type")
    st.json(s.get("entities_by_type", result.graph.entity_count_by_type()))

    # === NEW: Detailed view of loaded objects and their properties ===
    st.markdown("## 🔍 Detailed Loaded Objects")

    if result.graph.entities:
        # Group entities by type
        from collections import defaultdict
        entities_by_type = defaultdict(list)
        for e in result.graph.entities:
            entities_by_type[e.type].append(e)

        for entity_type, entities in sorted(entities_by_type.items()):
            with st.expander(f"**{entity_type.upper()}** ({len(entities)} items)", expanded=True):
                for i, entity in enumerate(entities[:50]):  # Limit to first 50 per type for performance
                    with st.container(border=True):
                        st.markdown(f"**ID:** `{entity.id[:12]}...`")
                        st.markdown(f"**Canonical Key:** `{entity.canonical_key}`")
                        
                        # Properties
                        st.markdown("**Properties:**")
                        if entity.properties:
                            # Nice display of properties
                            for k, v in entity.properties.items():
                                if isinstance(v, (dict, list)):
                                    st.json({k: v}, expanded=False)
                                else:
                                    st.write(f"- **{k}**: {v}")
                        else:
                            st.caption("No properties")

                        # Source refs
                        if entity.source_refs:
                            st.caption(f"Sources: {', '.join(entity.source_refs[:3])}")

                if len(entities) > 50:
                    st.caption(f"... and {len(entities) - 50} more {entity_type} entities")

    # Relationships summary
    if result.graph.relationships:
        st.markdown("### Relationships Overview")
        rel_types = {}
        for rel in result.graph.relationships:
            rel_types[rel.type] = rel_types.get(rel.type, 0) + 1
        st.json(rel_types)

    # Parser stats
    with st.expander("Parser Internal Statistics"):
        st.json(result.stats.get("parser_stats", {}))

    st.divider()

    # ==================== SEARCH ====================
    st.subheader("🔎 Search Entities")

    search_term = st.text_input("Search (name, phone, email, passport, etc.)", key="search")

    if search_term:
        matches = []
        term = search_term.lower()

        for e in result.graph.entities:
            props_str = json.dumps(e.properties, default=str).lower()
            if term in props_str or term in (e.canonical_key or "").lower():
                matches.append(e)

        st.write(f"Found **{len(matches)}** entities")

        for e in matches[:25]:
            with st.container(border=True):
                st.markdown(f"**{e.type}** — `{e.canonical_key or e.id[:8]}`")
                st.json({k: v for k, v in e.properties.items() if not isinstance(v, dict)})

    st.divider()

    # ==================== VISUAL GRAPH ====================
    st.subheader("🕸️ Relationship Graph Visualization")

    if st.button("Generate Interactive Graph", key="gen_graph"):
        try:
            from pyvis.network import Network
            import networkx as nx

            G = nx.DiGraph()

            for e in result.graph.entities:
                label = e.canonical_key or e.properties.get("full_name") or e.id[:8]
                G.add_node(e.id, label=label, type=e.type)

            for rel in result.graph.relationships:
                G.add_edge(rel.from_id, rel.to_id, label=rel.type)

            net = Network(height="700px", width="100%", directed=True, notebook=False)
            net.from_nx(G)
            net.repulsion(node_distance=120, spring_length=80)

            # Save to temp file and show
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                st.components.v1.html(open(tmp.name, encoding="utf-8").read(), height=720, scrolling=True)

            st.caption("Interactive graph (drag nodes, zoom). Built with pyvis + vis.js")

        except ImportError:
            st.error("Please install graph extras: pip install -e '.[graph]'")
        except Exception as e:
            st.error(f"Graph rendering failed: {e}")

    # Raw data export
    with st.expander("Export Options"):
        if st.button("Export Graph as JSON"):
            st.download_button(
                "Download graph.json",
                data=json.dumps(result.graph.to_dict(), indent=2, default=str),
                file_name="leak_graph.json",
                mime="application/json"
            )

else:
    st.info("Click **Run Import** in the sidebar to begin. The interface will become interactive after the first successful import.")

st.caption("Built for leak-data-importer • Dynamic framework • All data is kept in memory for this session")
