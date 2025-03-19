import streamlit as st
import subprocess

st.title("🚀 Manually Run Multiple Python Files in Streamlit")

# ✅ Button to Run `bhav.py`
if st.button("Run Bhav.py"):
    st.write("🔹 Running `bhav.py`...")

    # Execute `bhav.py` manually
    process = subprocess.Popen(
        ['python', 'bhav.py'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )

    # ✅ Display live logs
    st.write("### 📃 Output Logs:")
    stdout, stderr = process.communicate()
    
    # ✅ Show stdout
    if stdout:
        st.text(stdout)
    
    # ✅ Show stderr (if any)
    if stderr:
        st.error(f"⚠️ Error in `bhav.py`: {stderr}")
    else:
        st.success("✅ `bhav.py` executed successfully!")

# ✅ Button to Run `app.py`
if st.button("Run App.py"):
    st.write("🔹 Running `app.py`...")

    # Execute `app.py` manually
    process = subprocess.Popen(
        ['python', 'app.py'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )

    # ✅ Display live logs
    st.write("### 📃 Output Logs:")
    stdout, stderr = process.communicate()
    
    # ✅ Show stdout
    if stdout:
        st.text(stdout)
    
    # ✅ Show stderr (if any)
    if stderr:
        st.error(f"⚠️ Error in `app.py`: {stderr}")
    else:
        st.success("✅ `app.py` executed successfully!")
