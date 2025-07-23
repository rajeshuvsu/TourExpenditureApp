import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Tour Expenditure Split", page_icon="🏝️")

# Session state for expenses and known people
if 'expenses' not in st.session_state:
    st.session_state.expenses = []
if 'people' not in st.session_state:
    st.session_state.people = ["Person 1", "Person 2"]  # Editable

st.title("🏝️ Tour Expenditure Splitter")

with st.sidebar:
    st.header("People on Trip")
    # Add person
    new_person = st.text_input("Add a person", key="new_person")
    if st.button("Add Person"):
        if new_person and new_person not in st.session_state.people:
            st.session_state.people.append(new_person)
            st.success(f"Added {new_person}!")
        st.session_state.new_person = ""  # clear after add

    # Delete person (if needed)
    if st.session_state.people:
        person_to_remove = st.selectbox("Remove person", st.session_state.people, key="remove_person")
        if st.button("Remove Selected Person"):
            st.session_state.people.remove(person_to_remove)
            st.success(f"Removed {person_to_remove}")

# ---- Expense Entry Form ----
with st.form("Add Expense"):
    spend_date = st.date_input("Date", value=date.today())
    paid_by = st.selectbox("Paid By", st.session_state.people)
    category = st.selectbox("Category", ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"])
    amount = st.number_input("Amount (INR)", min_value=0.0, step=0.01, format="%.2f", key="amount")
    remarks = st.text_input("Remarks (optional)", key="remarks")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        st.session_state.expenses.append({
            "Date": spend_date,
            "Paid By": paid_by,
            "Category": category,
            "Amount (INR)": amount,
            "Remarks": remarks
        })
        # CLEAR form fields for new entry
        st.experimental_rerun()

if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.subheader("All Expenses")
    st.dataframe(df, use_container_width=True)

    st.subheader("Summary")
    total = df['Amount (INR)'].sum()
    st.metric("Total Spent", f"₹{total:,.2f}")

    st.bar_chart(df.groupby("Category")["Amount (INR)"].sum())

    # --- Settlement Calculation ---
    st.subheader("💸 Settlement")
    people = st.session_state.people
    paid = df.groupby("Paid By")["Amount (INR)"].sum().reindex(people, fill_value=0)
    share = total / len(people) if people else 0
    settlement_df = pd.DataFrame({
        "Paid (INR)": paid,
        "Should Pay Share (INR)": share,
        "Net (INR)": paid - share
    })
    settlement_df["Remarks"] = settlement_df["Net (INR)"].apply(
        lambda x: "To Receive" if x > 0 else ("Owes" if x < 0 else "Settled")
    )

    st.dataframe(settlement_df.style.format({
        "Paid (INR)": "₹{:.2f}",
        "Should Pay Share (INR)": "₹{:.2f}",
        "Net (INR)": "₹{:.2f}"
    }), use_container_width=True)

    # --- Excel Export ---
    def to_excel(data1, data2):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            data1.to_excel(writer, index=False, sheet_name='Expenses')
            data2.to_excel(writer, sheet_name='Settlement')
        return output.getvalue()
    excel_data = to_excel(df, settlement_df.reset_index())

    st.download_button(
        label="Download Expenses+Settlement as Excel",
        data=excel_data,
        file_name="tour_expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("Reset All Expenses"):
        st.session_state.expenses.clear()
        st.warning("All expenses reset.")
else:
    st.info("No expenses recorded yet. Add your first expense above!")
