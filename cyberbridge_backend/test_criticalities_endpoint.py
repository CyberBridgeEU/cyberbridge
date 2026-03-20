import requests
import json

# Test the criticalities endpoint
def test_criticalities_endpoint():
    url = "http://localhost:8000/products/criticalities"
    
    # You'll need to add authentication headers if required
    # For now, let's test without auth to see if the endpoint structure works
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Success! Response data:")
            print(json.dumps(data, indent=2))
            
            # Validate the structure
            if isinstance(data, list):
                print(f"\nFound {len(data)} criticalities")
                for i, criticality in enumerate(data):
                    print(f"Criticality {i+1}:")
                    print(f"  ID: {criticality.get('id')}")
                    print(f"  Label: {criticality.get('label')}")
                    print(f"  Options count: {len(criticality.get('options', []))}")
                    
                    # Show first few options
                    options = criticality.get('options', [])
                    for j, option in enumerate(options[:3]):
                        print(f"    Option {j+1}: {option.get('value', '')[:50]}...")
                    if len(options) > 3:
                        print(f"    ... and {len(options) - 3} more options")
            else:
                print("Unexpected response format - not a list")
                
        elif response.status_code == 401:
            print("Authentication required - this is expected")
            print("The endpoint structure should be working, just needs auth")
        else:
            print(f"Error response:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure the backend is running on localhost:8000")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_criticalities_endpoint()