import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Tour Group Expenditure Splitter", page_icon="🏝️")

# ------ INITIALIZE STATE ------
if "groups" not in st.session_state:
    st.session_state.groups = {
        "Group 1": {
            "people": ["Person 1", "Person 2"],
            "expenses": []
        }
    }
if "active_group" not in st.session_state:
    st.session_state.active_group = "Group 1"
if "new_group_name" not in st.session_state:
    st.session_state.new_group_name = ""
if "person_input" not in st.session_state:
    st.session_state.person_input = ""

# ------ GROUP MANAGEMENT ------
st.sidebar.subheader("Travel Groups")
new_group = st.sidebar.text_input("Create a new group", value=st.session_state.new_group_name, key="new_group_name")
add_group_clicked = st.sidebar.button("Add Group", key="add_group_btn")
if add_group_clicked:
    if new_group and new_group not in st.session_state.groups:
        st.session_state.groups[new_group] = {"people": [], "expenses": []}
        st.session_state.active_group = new_group
        st.session_state.new_group_name = ""  # clear!
        st.experimental_rerun()  # makes sure field is blank after adding
    elif new_group in st.session_state.groups:
        st.warning("Group already exists.")
    else:
        st.warning("Please enter a valid group name.")

all_groups = list(st.session_state.groups.keys())
if len(all_groups) > 1:
    if st.sidebar.button("Delete Current Group", key="delete_group_btn", help="Deletes the currently active group"):
        del st.session_state.groups[st.session_state.active_group]
        st.session_state.active_group = list(st.session_state.groups.keys())[0]
        st.experimental_rerun()

# --- Switch group
selected_group = st.sidebar.selectbox(
    "Choose active group",
    all_groups,
    key="group_select",
    index=all_groups.index(st.session_state.active_group) if st.session_state.active_group in all_groups else 0
)
if selected_group != st.session_state.active_group:
    st.session_state.active_group = selected_group
g = st.session_state.groups[st.session_state.active_group]

st.sidebar.markdown(f"**Active Group:** {st.session_state.active_group}")

# ------ PEOPLE MANAGEMENT ------
st.sidebar.markdown("### People in this group")
person_name = st.sidebar.text_input("Add a person (unique)", value=st.session_state.person_input, key="person_input")
add_person_clicked = st.sidebar.button("Add Person", key="add_person_btn")
if add_person_clicked:
    if person_name and person_name not in g["people"]:
        g["people"].append(person_name)
        st.session_state.person_input = ""  # clear!
        st.experimental_rerun()
    elif person_name in g["people"]:
        st.warning("That person already exists for this group.")
    else:
        st.warning("Please enter a valid person name.")

if g["people"]:
    remove_person = st.sidebar.selectbox("Remove person", g["people"], key="remove_person_select")
    if st.sidebar.button("Remove Selected Person", key="remove_person_btn"):
        g["people"].remove(remove_person)
        st.success(f"Removed {remove_person}")
else:
    st.sidebar.info("Add at least one person to this group.")

# ------ MAIN UI ------
st.title("🏝️ Tour Group Expenditure Splitter")
st.markdown(f"**Managing group:** `{st.session_state.active_group}`")

# ------ EXPENSE ENTRY ------
with st.form("add_expense_form", clear_on_submit=True):
    spend_date = st.date_input("Date", value=date.today())
    paid_by = st.selectbox("Paid By", g["people"] if g["people"] else [""], disabled=not bool(g["people"]))
    category = st.selectbox("Category", ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"])
    amount = st.number_input("Amount (INR)", min_value=0.0, step=0.01, format="%.2f")
    remarks = st.text_input("Remarks (optional)")
    submitted = st.form_submit_button("Add Expense")
    if submitted and paid_by:
        g["expenses"].append({
            "Date": spend_date,
            "Paid By": paid_by,
            "Category": category,
            "Amount (INR)": amount,
            "Remarks": remarks
        })
        st.success("Expense added!")

# ------ SETTLEMENT ALGORITHM ------
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

# ------ MAIN CONTENT ------
if g["expenses"]:
    expenses_df = pd.DataFrame(g["expenses"])

    st.subheader("All Expenses (double-click to edit in table and save)")
    edited_df = st.data_editor(
        expenses_df,
        num_rows="dynamic",
        key=f"data_editor_{st.session_state.active_group}",
        use_container_width=True,
        hide_index=True
    )

    # Always use the latest edited data for all calculations!
    if not edited_df.equals(expenses_df):
        g["expenses"] = edited_df.astype(expenses_df.dtypes).to_dict("records")
    expenses_to_use = edited_df.copy()

    # --- Amount Validation for Each Row ---
    invalid_rows = expenses_to_use[expenses_to_use["Amount (INR)"] <= 0]
    if not invalid_rows.empty:
        for idx, row in invalid_rows.iterrows():
            st.error(f"Enter valid amount for {row['Paid By']} (Row {idx+1}). Amount must be positive.")
        valid_data_for_export = False
    else:
        valid_data_for_export = True

    st.subheader("Summary")
    total = expenses_to_use["Amount (INR)"].sum()
    st.metric("Total Spent", f"₹{total:,.2f}")
    st.bar_chart(expenses_to_use.groupby("Category")["Amount (INR)"].sum())

    # ---- Settlement balances
    st.subheader("💸 Settlement balances")
    people = g["people"]
    paid = expenses_to_use.groupby("Paid By")["Amount (INR)"].sum().reindex(people, fill_value=0)
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
    st.dataframe(
        settlement_df.style.format({
            "Paid (INR)": "₹{:.2f}",
            "Should Pay Share (INR)": "₹{:.2f}",
            "Net (INR)": "₹{:.2f}"
        }),
        use_container_width=True
    )

    # ---- Who pays whom
    settlements = calculate_settlements(settlement_df)
    settlements_for_excel = pd.DataFrame(settlements) if settlements else pd.DataFrame(columns=["From", "To", "Amount (INR)"])

    if settlements:
        st.subheader("🧾 Who Should Pay Whom")
        st.table(settlements_for_excel)
    else:
        st.success("All accounts are settled. No payments needed.")

    # ---- Export to Excel with both settlement tables
    def to_excel(balances, whopaywhom):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            balances.to_excel(writer, index=False, sheet_name='SettlementBalances')
            whopaywhom.to_excel(writer, index=False, sheet_name='WhoShouldPayWhom')
        return output.getvalue()

    excel_data = to_excel(settlement_df, settlements_for_excel)

    if valid_data_for_export:
        st.download_button(
            label="Download Settlement Balances & Who-Pays-Whom (Excel)",
            data=excel_data,
            file_name=f"{st.session_state.active_group}_settlements.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.button(
            "Download Settlement Balances & Who-Pays-Whom (Excel) [Fix Invalid Amounts]",
            disabled=True
        )

    if st.button("Reset All Expenses", key="reset_exp_btn"):
        g["expenses"].clear()
        st.warning("All expenses reset.")

else:
    st.info("No expenses recorded yet. Add your first expense above!")
