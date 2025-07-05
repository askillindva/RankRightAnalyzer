import streamlit as st

def show_azure_firewall_error():
    """Display detailed Azure firewall configuration instructions"""
    
    st.error("🚫 Azure OpenAI Access Blocked")
    
    st.markdown("""
    **The error you're seeing means your Azure OpenAI service has firewall rules blocking this connection.**
    
    ### Quick Fix Instructions:
    
    1. **Go to Azure Portal** (portal.azure.com)
    2. **Find your Azure OpenAI resource**
    3. **Click on "Networking" in the left sidebar**
    4. **Under "Firewalls and virtual networks":**
       - Currently set to: "Selected networks" 
       - **Change to: "All networks"** (easiest option)
       - OR add your current IP to the allowed list
    5. **Click "Save"**
    6. **Wait 2-3 minutes** for changes to take effect
    7. **Try uploading and analyzing a document again**
    
    ### Alternative Solution:
    If you need to keep network restrictions, you can add the current IP address to your allowed list in Azure.
    
    ### Security Note:
    "All networks" allows access from anywhere. If security is important, use IP restrictions instead.
    """)
    
    with st.expander("📋 Detailed Step-by-Step Guide"):
        st.markdown("""
        **Step 1: Access Azure Portal**
        - Go to https://portal.azure.com
        - Sign in with your Azure account
        
        **Step 2: Navigate to Your OpenAI Resource**
        - In the search bar, type "OpenAI"
        - Click on your Azure OpenAI resource
        
        **Step 3: Open Networking Settings**
        - In the left menu, scroll down and click "Networking"
        - You'll see "Firewalls and virtual networks" section
        
        **Step 4: Change Network Access**
        - You'll see it's currently set to "Selected networks"
        - Select "All networks" radio button
        - Click "Save" at the top
        
        **Step 5: Wait and Test**
        - Wait 2-3 minutes for Azure to apply changes
        - Return to RankRight and try analyzing a document
        """)

def show_connection_test_section():
    """Show connection testing section"""
    
    st.subheader("🔍 Test Your Connection")
    
    if st.button("Test Azure OpenAI Connection", type="primary"):
        try:
            from azure_openai_client import AzureOpenAIClient
            client = AzureOpenAIClient()
            
            # Try a simple test
            if client.test_connection():
                st.success("✅ Connection successful! Your Azure OpenAI is working.")
                st.info("You can now go back to the Home page and try analyzing documents.")
            else:
                st.error("❌ Connection still failing. Please check your Azure settings.")
                show_azure_firewall_error()
                
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Virtual Network" in error_msg or "Firewall" in error_msg:
                show_azure_firewall_error()
            else:
                st.error(f"Connection error: {error_msg}")