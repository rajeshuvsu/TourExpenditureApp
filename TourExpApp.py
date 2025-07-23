import streamlit as st
import pandas as pd
import io
from datetime import date

if 'expenses' not in st.session_state:
    st.session_state.expenses = []

st.title("🏝️ Tour Expenditure Tracker")

with st.form("Add Expense"):
    spend_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"])
    amount = st.number_input("Amount (INR)", min_value=0.0, step=0.01, format="%.2f")
    remarks = st.text_input("Remarks (optional)")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        st.session_state.expenses.append({
            "Date": spend_date,
            "Category": category,
            "Amount (INR)": amount,
            "Remarks": remarks
        })
        st.success("Expense added!")

if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.subheader("All Expenses")
    st.dataframe(df)

    st.subheader("Summary")
    total = df['Amount (INR)'].sum()
    st.metric("Total Spent", f"₹{total:,.2f}")

    st.bar_chart(df.groupby("Category")["Amount (INR)"].sum())

    # Export to Excel
    def to_excel(df):
       output = io.BytesIO()
       with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Expenses')
       # No writer.save()
       return output.getvalue()

    excel_data = to_excel(df)
    st.download_button(
        label="Download Expenses as Excel",
        data=excel_data,
        file_name="tour_expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.button("Reset All Expenses"):
        st.session_state.expenses.clear()
        st.warning("All expenses reset.")
else:
    st.info("No expenses recorded yet. Add your first expense above!")
