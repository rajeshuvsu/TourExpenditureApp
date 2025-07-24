# --- GROUP MANAGEMENT ---
st.sidebar.subheader("Travel Groups")

if "new_group_name" not in st.session_state:
    st.session_state["new_group_name"] = ""

new_group = st.sidebar.text_input("Create a new group", key="new_group_name")
add_group_clicked = st.sidebar.button("Add Group", key="add_group_btn")
group_added = False

if add_group_clicked:
    if new_group and new_group not in st.session_state.groups:
        st.session_state.groups[new_group] = {"people": [], "expenses": []}
        st.session_state.active_group = new_group
        group_added = True
        st.session_state["new_group_name"] = ""   # Clear input!
        st.experimental_rerun()                   # Forces UI refresh so box is empty on next draw
    elif new_group in st.session_state.groups:
        st.warning("Group already exists.")
    else:
        st.warning("Please enter a valid group name.")

# Only show Delete Group if >1 group
all_groups = list(st.session_state.groups.keys())
if len(all_groups) > 1:
    if st.sidebar.button("Delete Current Group", key="delete_group_btn", help="Deletes the currently active group"):
        del st.session_state.groups[st.session_state.active_group]
        st.session_state.active_group = list(st.session_state.groups.keys())[0]
        st.rerun()
