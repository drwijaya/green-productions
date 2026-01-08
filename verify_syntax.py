
try:
    from app.services.qc_analytics import QCAnalyticsService
    print("QCAnalyticsService imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
except SyntaxError as e:
    print(f"SyntaxError in qc_analytics: {e}")
except Exception as e:
    # It might fail due to database connection not configured, which is expected
    print(f"Other error (expected potentially): {e}")

try:
    # app/views/__init__.py imports many things, might fail to import due to missing full context, 
    # but we can try to parse it.
    with open('app/views/__init__.py', 'r') as f:
        compile(f.read(), 'app/views/__init__.py', 'exec')
    print("views/__init__.py compiled successfully")
except Exception as e:
    print(f"Error compiling views: {e}")
