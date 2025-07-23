import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Tour Group Expenditure Split", page_icon="🏝️")

# Initialize all group data in session state
if "groups" not in st.session_state:
    st.session_state.groups = {
        "Group 1": {
            "people": ["Person 1", "Person 2"],
            "expenses": []
        }
    }
if "active_group" not in st.session_state:
    st.session_state.active_group = "Group 1"

# --- GROUP MANAGEMENT ---
st.sidebar.subheader("Travel Groups")

# Create a new group
new_group = st.sidebar.text_input("Create a new group", key="new_group_name")
if st.sidebar.button("Add Group"):
    if new_group and new_group not in st.session_state.groups:
        st.session_state.groups[new_group] = {"people": [], "expenses": []}
        st.session_state.active_group = new_group
        st.success(f"Created group '{new_group}'!")
    elif new_group in st.session_state.groups:
        st.warning("Group already exists.")

# Select group
all_groups = list(st.session_state.groups.keys())
selected_group = st.sidebar.selectbox("Choose active group", all_groups, key="group_select", index=all_groups.index(st.session_state.active_group))
if selected_group != st.session_state.active_group:
    st.session_state.active_group = selected_group

# Access selected group's data
g = st.session_state.groups[st.session_state.active_group]

st.sidebar.markdown(f"**Active Group:** {st.session_state.active_group}")

# --- PEOPLE MANAGEMENT ---
st.sidebar.markdown("### People in this group")
person_name = st.sidebar.text_input("Add a person (unique)", key="person_input")
if st.sidebar.button("Add Person", key="add_person_btn"):
    if person_name and person_name not in g["people"]:
        g["people"].append(person_name)
        st.success(f"Added {person_name} to {st.session_state.active_group}!")
    elif person_name in g["people"]:
        st.warning("That person already exists for this group.")

if g["people"]:
    remove_person = st.sidebar.selectbox("Remove person", g["people"], key="remove_person_select")
    if st.sidebar.button("Remove Selected Person", key="remove_person_btn"):
        g["people"].remove(remove_person)
        st.success(f"Removed {remove_person}")

st.title("🏝️ Tour Group Expenditure Splitter")
st.markdown(f"**Managing group:** `{st.session_state.active_group}`")

# --- EXPENSE ENTRY ---
with st.form("add_expense_form", clear_on_submit=True):
    spend_date = st.date_input("Date", value=date.today(), key="expense_date")
    paid_by = st.selectbox("Paid By", g["people"], key="expense_paid_by")
    category = st.selectbox(
        "Category",
        ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"],
        key="expense_cat"
    )
    amount = st.number_input("Amount (INR)", min_value=0.0, step=0.01, format="%.2f", key="expense_amount")
    remarks = st.text_input("Remarks (optional)", key="expense_remarks")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        g["expenses"].append({
            "Date": spend_date,
            "Paid By": paid_by,
            "Category": category,
            "Amount (INR)": amount,
            "Remarks": remarks
        })
        st.success("Expense added!")

# --- MAIN CONTENT ---
if g["expenses"]:
    df = pd.DataFrame(g["expenses"])
    st.subheader("All Expenses")
    st.dataframe(df, use_container_width=True)

    st.subheader("Summary")
    total = df['Amount (INR)'].sum()
    st.metric("Total Spent", f"₹{total:,.2f}")

    st.bar_chart(df.groupby("Category")["Amount (INR)"].sum())

    # Settlement Calculation
    st.subheader("💸 Settlement")
    people = g["people"]
    paid = df.groupby("Paid By")["Amount (INR)"].sum().reindex(people, fill_value=0)
    n_people = len(people)
    share = total / n_people if n_people else 0
    net = paid - share
    settlement_df = pd.DataFrame({
        "Paid (INR)": paid,
        "Should Pay Share (INR)": share,
        "Net (INR)": net
    })
    settlement_df["Remarks"] = settlement_df["Net (INR)"].apply(
        lambda x: "To Receive" if x > 0 else ("Owes" if x < 0 else "Settled")
    )

    st.dataframe(settlement_df.style.format({
        "Paid (INR)": "₹{:.2f}",
        "Should Pay Share (INR)": "₹{:.2f}",
        "Net (INR)": "₹{:.2f}"
    }), use_container_width=True)

    # Excel Export
    def to_excel(data1, data2):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data1.to_excel(writer, index=False, sheet_name='Expenses')
            data2.to_excel(writer, sheet_name='Settlement')
        return output.getvalue()
    excel_data = to_excel(df, settlement_df.reset_index())

    st.download_button(
        label=f"Download Excel for {st.session_state.active_group}",
        data=excel_data,
        file_name=f"{st.session_state.active_group}_expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("Reset All Expenses", key="reset_exp_btn"):
        g["expenses"].clear()
        st.warning("All expenses reset.")
else:
    st.info("No expenses recorded yet. Add your first expense above!")

