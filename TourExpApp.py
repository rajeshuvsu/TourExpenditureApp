import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Tour Group Expenditure Split", page_icon="🏝️")

# --- STATE ---
if "groups" not in st.session_state:
    st.session_state.groups = {
        "Group 1": {
            "people": ["Person 1", "Person 2"],
            "expenses": []
        }
    }
if "active_group" not in st.session_state:
    st.session_state.active_group = "Group 1"
if "edit_row" not in st.session_state:
    st.session_state.edit_row = None  # (row index) if editing

# --- GROUP MANAGEMENT ---
st.sidebar.subheader("Travel Groups")
new_group = st.sidebar.text_input("Create a new group", key="new_group_name")
if st.sidebar.button("Add Group"):
    if new_group and new_group not in st.session_state.groups:
        st.session_state.groups[new_group] = {"people": [], "expenses": []}
        st.session_state.active_group = new_group
        st.success(f"Created group '{new_group}'!")
    elif new_group in st.session_state.groups:
        st.warning("Group already exists.")

all_groups = list(st.session_state.groups.keys())
selected_group = st.sidebar.selectbox(
    "Choose active group",
    all_groups,
    key="group_select",
    index=all_groups.index(st.session_state.active_group)
)
if selected_group != st.session_state.active_group:
    st.session_state.active_group = selected_group

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
else:
    st.sidebar.info("Add at least one person to this group.")

# --- MAIN UI ---
st.title("🏝️ Tour Group Expenditure Splitter")
st.markdown(f"**Managing group:** `{st.session_state.active_group}`")

# --- EXPENSE ENTRY ---
if g["people"] and st.session_state.edit_row is None:
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
elif st.session_state.edit_row is not None:
    # --- Edit Mode ---
    idx = st.session_state.edit_row
    expense = g["expenses"][idx]
    st.info(f"Editing Expense #{idx+1}")

    with st.form(f"edit_expense_form_{idx}"):
        spend_date = st.date_input("Date", value=expense["Date"], key=f"edit_date_{idx}")
        paid_by = st.selectbox("Paid By", g["people"], index=g["people"].index(expense["Paid By"]), key=f"edit_paidby_{idx}")
        category = st.selectbox("Category",
            ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"],
            index=["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"].index(expense["Category"]),
            key=f"edit_cat_{idx}")
        amount = st.number_input("Amount (INR)", min_value=0.0, value=expense["Amount (INR)"], step=0.01, format="%.2f", key=f"edit_amount_{idx}")
        remarks = st.text_input("Remarks (optional)", value=expense["Remarks"], key=f"edit_remarks_{idx}")
        edit_submit = st.form_submit_button("Update Expense")
        if edit_submit:
            g["expenses"][idx] = {
                "Date": spend_date,
                "Paid By": paid_by,
                "Category": category,
                "Amount (INR)": amount,
                "Remarks": remarks
            }
            st.success(f"Expense #{idx+1} updated.")
            st.session_state.edit_row = None

    if st.button("Cancel Edit", key="cancel_edit"):
        st.session_state.edit_row = None

# --- SETTLEMENT ALGORITHM ---
def calculate_settlements(df):
    creditors = []
    debtors = []
    for _, row in df.iterrows():
        person = row['Person']
        net = round(row['Net (INR)'], 2)
        if net > 0:
            creditors.append([person, net])
        elif net < 0:
            debtors.append([person, -net])
    settlements = []
    c, d = 0, 0
    while c < len(creditors) and d < len(debtors):
        creditor, cred_amt = creditors[c]
        debtor, debt_amt = debtors[d]
        settled_amt = min(cred_amt, debt_amt)
        settlements.append({
            "From": debtor,
            "To": creditor,
            "Amount (INR)": f"₹{settled_amt:,.2f}"
        })
        cred_amt -= settled_amt
        debt_amt -= settled_amt
        if abs(debt_amt) < 1e-6:
            d += 1
        else:
            debtors[d][1] = debt_amt
        if abs(cred_amt) < 1e-6:
            c += 1
        else:
            creditors[c][1] = cred_amt
    return settlements

# --- MAIN CONTENT ---
if g["expenses"]:
    df = pd.DataFrame(g["expenses"])

    # Inline actions
    st.subheader("All Expenses")
    edit_col, delete_col = st.columns([1, 1])
    for i, row in df.iterrows():
        c1, c2 = st.columns([12, 1])
        c1.write(
            f"**{row['Date']}**, {row['Category']} - ₹{row['Amount (INR)']:,.2f} paid by **{row['Paid By']}**{' | '+row['Remarks'] if row['Remarks'] else ''}"
        )
        if c2.button("✏️ Edit", key=f"edit_btn_{i}"):
            st.session_state.edit_row = i
            st.experimental_rerun()
        if c2.button("❌ Delete", key=f"del_btn_{i}"):
            g["expenses"].pop(i)
            st.success(f"Expense #{i+1} deleted.")
            st.experimental_rerun()

    st.divider()
    st.subheader("Summary")
    total = df['Amount (INR)'].sum()
    st.metric("Total Spent", f"₹{total:,.2f}")

    st.bar_chart(df.groupby("Category")["Amount (INR)"].sum())

    st.subheader("💸 Settlement balances")
    people = g["people"]
    paid = df.groupby("Paid By")["Amount (INR)"].sum().reindex(people, fill_value=0)
    n_people = len(people)
    share = total / n_people if n_people else 0
    net = paid - share
    settlement_df = pd.DataFrame({
        "Person": people,
        "Paid (INR)": paid.tolist(),
        "Should Pay Share (INR)": [share] * n_people,
        "Net (INR)": net.tolist()
    })
    settlement_df["Remarks"] = settlement_df["Net (INR)"].apply(
        lambda x: "To Receive" if x > 0 else ("Owes" if x < 0 else "Settled")
    )

    st.dataframe(settlement_df.style.format({
        "Paid (INR)": "₹{:.2f}",
        "Should Pay Share (INR)": "₹{:.2f}",
        "Net (INR)": "₹{:.2f}",
    }), use_container_width=True)

    # --- Who pays whom ---
    settlements = calculate_settlements(settlement_df)
    if settlements:
        st.subheader("🧾 Who Should Pay Whom")
        settlements_df = pd.DataFrame(settlements)
        settlements_df["Amount (INR)"] = settlements_df["Amount (INR)"].apply(lambda x: f"{x}")
        st.table(settlements_df)
    else:
        st.success("All accounts are settled. No payments needed.")

    # Excel Export
    def to_excel(data1, data2, data3):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data1.to_excel(writer, index=False, sheet_name='Expenses')
            data2.to_excel(writer, index=False, sheet_name='Summary')
            data3.to_excel(writer, index=False, sheet_name='WhoPaysWhom')
        return output.getvalue()
    settlements_for_excel = pd.DataFrame(settlements) if settlements else pd.DataFrame(columns=["From", "To", "Amount (INR)"])
    excel_data = to_excel(df, settlement_df, settlements_for_excel)

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
