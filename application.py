from apps import create_app
import sys

application = create_app()
 
if __name__ == "__main__":
    if "--test" in sys.argv:
        print("Running in TEST mode with MockDynamoDB")
        application.run(debug=True, port=5000)
    else:
        application.run()
