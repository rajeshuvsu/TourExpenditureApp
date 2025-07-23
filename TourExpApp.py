import streamlit as st
import pandas as pd
import io
from datetime import date
import dropbox
import os

# --- Initialize expenses in session state ---
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

st.title("🏝️ Tour Expenditure Tracker")

# Expense entry form
with st.form("Add Expense"):
    spend_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Transport", "Accommodation", "Food", "Activities", "Shopping", "Other"])
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
    remarks = st.text_input("Remarks (optional)")
    submitted = st.form_submit_button("Add Expense")
    if submitted:
        st.session_state.expenses.append({
            "Date": spend_date,
            "Category": category,
            "Amount": amount,
            "Remarks": remarks
        })
        st.success("Expense added!")

# Show expenses if any
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.subheader("All Expenses")
    st.dataframe(df)

    # Summary
    st.subheader("Summary")
    total = df['Amount'].sum()
    st.metric("Total Spent", f"${total:,.2f}")

    st.bar_chart(df.groupby("Category")["Amount"].sum())

    # Export to Excel
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Expenses')
            writer.save()
        processed_data = output.getvalue()
        return processed_data

    excel_data = to_excel(df)

    st.download_button(
        label="Download Expenses as Excel",
        data=excel_data,
        file_name="tour_expenses.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Dropbox upload feature
    st.subheader("Upload to Dropbox Cloud (Optional)")

    # You can set your Dropbox token as environment variable DROPBOX_TOKEN
    dropbox_token = os.getenv("DROPBOX_TOKEN", "")

    if not dropbox_token:
        dropbox_token = st.text_input(
            "Enter your Dropbox Access Token (or set DROPBOX_TOKEN environment variable)", type="password"
        )

    if dropbox_token:
        if st.button("Upload Excel to Dropbox"):
            try:
                dbx = dropbox.Dropbox(dropbox_token)
                path = f"/tour_expenses_{date.today().isoformat()}.xlsx"
                dbx.files_upload(excel_data, path, mode=dropbox.files.WriteMode.overwrite)
                st.success(f"File uploaded to your Dropbox at {path}")
            except Exception as e:
                st.error(f"Dropbox upload failed: {e}")

    # Reset expenses
    if st.button("Reset All Expenses"):
        st.session_state.expenses.clear()
        st.warning("All expenses reset.")
else:
    st.info("No expenses recorded yet. Add your first expense above!")
