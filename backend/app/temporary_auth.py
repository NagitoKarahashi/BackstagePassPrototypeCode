from supabase import create_client

url = "https://nstagmuijwppjbsvpcwc.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5zdGFnbXVpandwcGpic3ZwY3djIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI5NTc1MDAsImV4cCI6MjA4ODUzMzUwMH0.4CT5Axlc3uE40nBErbPRhXefJHUMDgm-txGJEAsfvwU"

sb = create_client(url, key)

try:
    resp = sb.auth.sign_in_with_password({
        "email": "tanzhi2004@gmail.com",
        "password": "qwerty123"
    })
    print("Login success")
    # print(resp)
    print(resp.session.access_token)
except Exception as e:
    print("Login failed:", e)

