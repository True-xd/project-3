import sqlite3
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("issues.db")
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute("""
              CREATE TABLE IF NOT EXISTS issues
              (
                  id
                  INTEGER
                  PRIMARY
                  KEY
                  AUTOINCREMENT,
                  title
                  TEXT,
                  description
                  TEXT,
                  location
                  TEXT,
                  status
                  TEXT
              )
              """)
    conn.commit()

    # Check if 'priority' column exists
    c.execute("PRAGMA table_info(issues)")
    columns = [col[1] for col in c.fetchall()]
    if 'priority' not in columns:
        c.execute("ALTER TABLE issues ADD COLUMN priority TEXT DEFAULT 'Medium'")
        conn.commit()

    conn.close()


def add_issue(title, description, location, priority):
    conn = sqlite3.connect("issues.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO issues (title, description, location, status, priority) VALUES (?, ?, ?, ?, ?)",
        (title, description, location, "Pending", priority)
    )
    issue_id = c.lastrowid  # Get the inserted row ID
    conn.commit()
    conn.close()
    return issue_id


def get_issues():
    conn = sqlite3.connect("issues.db")
    df = pd.read_sql_query("SELECT * FROM issues", conn)
    conn.close()
    return df


def update_status(issue_id, status):
    conn = sqlite3.connect("issues.db")
    c = conn.cursor()
    c.execute("UPDATE issues SET status=? WHERE id=?", (status, issue_id))
    conn.commit()
    conn.close()


# ---------- INIT ----------
init_db()

# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Citizen"
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_password" not in st.session_state:
    st.session_state.admin_password = ""

# ---------- PAGE SETTINGS ----------
st.set_page_config(page_title="CIVIC ISSUE SUBMISSION", layout="wide")

# ---- CUSTOM CSS ----
st.markdown("""
<style>
.header-block {
    background-color:#3498db;color:white;
    padding:15px 30px;border-radius:8px;
    text-align:center;font-size:32px;font-weight:bold;
    margin-bottom:20px;
}
.section-title { color:#2980b9;font-size:24px;border-bottom:2px solid #3498db;padding-bottom:5px;margin-top:25px; }
.metric-card {
    background-color:white;padding:15px;
    border-radius:12px;
    box-shadow:0 4px 8px rgba(0,0,0,0.05);
    text-align:center;
}
.status-badge {
    padding:2px 8px;border-radius:8px;color:white;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ---- JAVASCRIPT FADE-IN ----
components.html("""
<script>
document.addEventListener("DOMContentLoaded", () => {
    document.body.style.opacity = 0;
    setTimeout(() => {
        document.body.style.transition = "opacity 1.2s";
        document.body.style.opacity = 1;
    }, 50);
});
</script>
""", height=0)

# ---- HEADER ----
st.markdown("<div class='header-block'>CIVIC ISSUE SUBMISSION</div>", unsafe_allow_html=True)

# ---- LEFT SIDE ROLE BUTTONS ----
left_col, right_col = st.columns([1, 5])
with left_col:
    st.markdown("### Select")
    if st.button("🏠 Citizen"):
        st.session_state.page = "Citizen"
    if st.button("🛠️ Admin"):
        st.session_state.page = "Admin"

with right_col:
    # ---------- CITIZEN PAGE ----------
    if st.session_state.page == "Citizen":
        st.markdown("<div class='section-title'>📋 Submit a New Issue</div>", unsafe_allow_html=True)
        title = st.text_input("Issue Title")
        description = st.text_area("Description")
        location = st.text_input("Location")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        if st.button("Submit Issue"):
            if title and location:
                issue_id = add_issue(title, description, location, priority)
                st.success(f"✅ Issue submitted successfully! Your Issue ID is: **{issue_id}**")
                components.html("""<script>alert('Your issue has been submitted successfully!');</script>""", height=0)
            else:
                st.warning("Please fill in the Title and Location")

        # --- Issue Viewing System by ID ---
        st.markdown("<div class='section-title'>🔍 View Your Issue by ID</div>", unsafe_allow_html=True)
        view_id = st.text_input("Enter Issue ID to view")
        if view_id:
            if view_id.isdigit():
                df = get_issues()
                issue = df[df['id'] == int(view_id)]
                if not issue.empty:
                    issue = issue.iloc[0]
                    st.markdown(f"**Issue ID:** {issue['id']}")
                    st.markdown(f"**Title:** {issue['title']}")
                    st.markdown(f"**Description:** {issue['description']}")
                    st.markdown(f"**Location:** {issue['location']}")
                    st.markdown(f"**Priority:** {issue['priority']}")
                    st.markdown(f"**Status:** {issue['status']}")
                else:
                    st.warning("No issue found with that ID.")
            else:
                st.warning("Please enter a valid numeric Issue ID.")

    # ---------- ADMIN PAGE ----------
    elif st.session_state.page == "Admin":
        st.markdown("<div class='section-title'>🛠️ Admin Dashboard</div>", unsafe_allow_html=True)
        PASSWORD = "admin123"

        # Admin login
        if not st.session_state.admin_logged_in:
            st.session_state.admin_password = st.text_input("Enter Admin Password", type="password",
                                                            value=st.session_state.admin_password)
            if st.button("Unlock Admin Panel"):
                if st.session_state.admin_password == PASSWORD:
                    st.session_state.admin_logged_in = True
                    st.success("✅ Access granted")
                    components.html("""<script>alert('Admin access granted!');</script>""", height=0)
                else:
                    st.error("❌ Incorrect password")
                    components.html("""<script>alert('Wrong password! Access denied.');</script>""", height=0)

        # Admin panel content
        if st.session_state.admin_logged_in:
            if st.button("🔒 Logout"):
                st.session_state.admin_logged_in = False
                st.session_state.page = "Citizen"

            df = get_issues()
            if not df.empty:
                # Sidebar filters
                st.sidebar.markdown("### Filters & Search")
                status_filter = st.sidebar.selectbox("Filter by Status", ["All", "Pending", "In Progress", "Resolved"])
                priority_filter = st.sidebar.selectbox("Filter by Priority", ["All", "High", "Medium", "Low"])
                search_query = st.sidebar.text_input("Search by Title or Location").lower()

                filtered_df = df if status_filter == "All" else df[df['status'] == status_filter]
                filtered_df = filtered_df if priority_filter == "All" else filtered_df[
                    filtered_df['priority'] == priority_filter]
                if search_query:
                    filtered_df = filtered_df[filtered_df['title'].str.lower().str.contains(search_query) |
                                              filtered_df['location'].str.lower().str.contains(search_query)]

                # Metrics
                total_issues = len(filtered_df)
                pending_issues = len(filtered_df[filtered_df['status'] == "Pending"])
                in_progress_issues = len(filtered_df[filtered_df['status'] == "In Progress"])
                resolved_issues = len(filtered_df[filtered_df['status'] == "Resolved"])

                st.markdown("### Dashboard Overview")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(f"<div class='metric-card'>Total Issues<br><b>{total_issues}</b></div>",
                                unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div class='metric-card'>Pending<br><b>{pending_issues}</b></div>",
                                unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='metric-card'>In Progress<br><b>{in_progress_issues}</b></div>",
                                unsafe_allow_html=True)
                with c4:
                    st.markdown(f"<div class='metric-card'>Resolved<br><b>{resolved_issues}</b></div>",
                                unsafe_allow_html=True)

                # Filtered Issues Table with colored badges
                st.markdown("<div class='section-title'>📅 Filtered Issues</div>", unsafe_allow_html=True)


                def status_badge(status):
                    color = {"Pending": "#f1c40f", "In Progress": "#3498db", "Resolved": "#2ecc71"}.get(status,
                                                                                                        "#bdc3c7")
                    return f"<span class='status-badge' style='background-color:{color}'>{status}</span>"


                def priority_badge(priority):
                    color = {"High": "#e74c3c", "Medium": "#e67e22", "Low": "#2ecc71"}.get(priority, "#bdc3c7")
                    return f"<span class='status-badge' style='background-color:{color}'>{priority}</span>"


                filtered_df['Status_Badge'] = filtered_df['status'].apply(status_badge)
                filtered_df['Priority_Badge'] = filtered_df['priority'].apply(priority_badge)

                display_df = filtered_df[
                    ['id', 'title', 'description', 'location', 'Priority_Badge', 'Status_Badge']].rename(
                    columns={'Priority_Badge': 'Priority', 'Status_Badge': 'Status'}
                )
                st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)

                # Update Status
                if not filtered_df.empty:
                    selected_id = st.selectbox("Select Issue ID to update", filtered_df['id'])
                    new_status = st.selectbox("New Status", ["Pending", "In Progress", "Resolved"])
                    if st.button("Update Status"):
                        update_status(selected_id, new_status)
                        st.success("✅ Status updated")
                        components.html("""<script>alert('Issue status has been updated!');</script>""", height=0)
            else:
                st.info("No issues reported yet.")
