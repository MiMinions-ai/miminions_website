from apps import create_app

# Create the application configuration
# This calls get_config() internally which checks for local/test flags
application = create_app()

if __name__ == "__main__":
    application.run()
