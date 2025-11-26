import streamlit as st
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import re
import io
import base64



# --- CONFIGURATION ---
# Ideally, store these in st.secrets for production apps
SENDER_EMAIL = "xu887599@gmail.com"
SENDER_PASSWORD = "gvfm vomn okcw ldgo"  # Replace with your app password 
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
BACKGROUND_IMAGE_PATH = "USCLogo.png"

st.set_page_config(page_title="Streamlit Photo Booth", page_icon="📸", layout="centered")

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'captured_images' not in st.session_state:
    st.session_state.captured_images = [] 

def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Make main container semi-transparent to show BG */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: rem;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def validate_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    return re.fullmatch(regex, email)

def send_email(to_emails, images_to_send):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = "📸 Your Streamlit Photo Booth Pictures!"
        
        body = "Here are the photos you selected from your session."
        msg.attach(MIMEText(body, 'plain'))

        for i, img_bytes in enumerate(images_to_send):
            # Create a MIME image object from the bytes
            image_data = MIMEImage(img_bytes, name=f"photo_{i+1}.jpg")
            msg.attach(image_data)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_emails, msg.as_string())
        server.quit()
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

def reset_app():
    st.session_state.step = 1
    st.session_state.captured_images = []
    st.session_state.user_email = ""

try:
    add_bg_from_local(BACKGROUND_IMAGE_PATH)
except FileNotFoundError:
    st.error(f"Background image '{BACKGROUND_IMAGE_PATH}' not found. Please ensure it's in the same directory.")

st.title("📸 Streamlit Photo Booth")

if st.session_state.step == 1:
    st.subheader("Step 1: Enter your Email")
    
    email_input = st.text_input("Email Address", placeholder="you@example.com")
    
    if st.button("Start Session"):
        if validate_email(email_input):
            st.session_state.user_email = email_input
            st.session_state.step = 2
            st.rerun()
        else:
            st.error("Please enter a valid email address.")

elif st.session_state.step == 2:
    st.subheader("Step 2: Capture Photos")
    st.write(f"Logged in as: **{st.session_state.user_email}**")

 # The Camera Input
    # Note: Streamlit re-runs the script when a photo is taken.
    if 'camera_key' not in st.session_state:
        st.session_state.camera_key = 0
    
    # Camera widget with dynamic key to auto-clear after saving
    img_buffer = st.camera_input("Take a picture", key=f"camera_{st.session_state.camera_key}")


    if img_buffer is not None:
        bytes_data = img_buffer.getvalue()
        if bytes_data not in st.session_state.captured_images:
            st.session_state.captured_images.append(bytes_data)
            st.toast("Photo saved!", icon="✅")
            # Increment camera key to reset widget
            st.session_state.camera_key += 1
            st.rerun()
    if st.session_state.captured_images:
        st.write("---")
        st.write(f"**Captured: {len(st.session_state.captured_images)} photos**")
        
        cols = st.columns(3)
        for i, img_data in enumerate(st.session_state.captured_images):
            with cols[i % 3]:
                st.image(img_data, caption=f"Photo {i+1}", use_container_width=True)

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear All Photos"):
            st.session_state.captured_images = []
            st.rerun()
    with col2:
        if st.button("Proceed to Review", type="primary"):
            if not st.session_state.captured_images:
                st.warning("Take at least one photo first!")
            else:
                st.session_state.step = 3
                st.rerun()

elif st.session_state.step == 3:
    st.subheader("Step 3: Select & Send")
    
    with st.form("selection_form"):
        st.write("Select the photos you want to keep:")
        
        selected_indices = []
        
        cols = st.columns(3)
        for i, img_data in enumerate(st.session_state.captured_images):
            with cols[i % 3]:
                st.image(img_data, use_container_width=True)
                if st.checkbox(f"Keep Photo {i+1}", value=True, key=f"chk_{i}"):
                    selected_indices.append(i)
        
        st.write("---")
        st.write("### Email Details")
        
        recipients = st.text_input("Send to (comma separated)", value=st.session_state.user_email)
        
        submitted = st.form_submit_button("Send Photos", type="primary")
        
        if submitted:
            if not selected_indices:
                st.error("Please select at least one photo to send.")
            else:
                final_images = [st.session_state.captured_images[i] for i in selected_indices]
                recipient_list = [r.strip() for r in recipients.split(",")]
                
                with st.spinner("Sending email..."):
                    success, message = send_email(recipient_list, final_images)
                
                if success:
                    st.success(message)
                    st.balloons()

                else:
                    st.error(f"Error: {message}")

    if st.button("Start Over"):
        reset_app()
        st.rerun()