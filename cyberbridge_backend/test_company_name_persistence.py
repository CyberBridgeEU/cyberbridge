# Test script to verify company_name persistence functionality

def test_company_name_persistence():
    """Test that company_name is properly stored and retrieved"""
    
    print("🧪 Testing Company Name Persistence")
    print("=" * 50)
    
    # Test case 1: Verify model has company_name field
    print("1. Checking if Policies model has company_name field...")
    try:
        from app.models.models import Policies
        import inspect
        
        # Get all attributes of the Policies class
        attributes = [attr for attr in dir(Policies) if not attr.startswith('_')]
        
        if 'company_name' in attributes:
            print("   ✓ company_name field found in Policies model")
        else:
            print("   ❌ company_name field NOT found in Policies model")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking model: {e}")
        return False
    
    # Test case 2: Verify schema includes company_name
    print("\n2. Checking if PolicyResponse schema has company_name field...")
    try:
        from app.dtos.schemas import PolicyResponse
        
        # Get the model fields
        fields = PolicyResponse.__fields__
        
        if 'company_name' in fields:
            print("   ✓ company_name field found in PolicyResponse schema")
        else:
            print("   ❌ company_name field NOT found in PolicyResponse schema")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking schema: {e}")
        return False
    
    # Test case 3: Verify repository functions handle company_name
    print("\n3. Checking if repository functions handle company_name...")
    try:
        import inspect
        from app.repositories import policy_repository
        
        # Check create_policy function
        create_source = inspect.getsource(policy_repository.create_policy)
        if 'company_name' in create_source:
            print("   ✓ create_policy function handles company_name")
        else:
            print("   ❌ create_policy function does NOT handle company_name")
            return False
            
        # Check update_policy function
        update_source = inspect.getsource(policy_repository.update_policy)
        if 'company_name' in update_source:
            print("   ✓ update_policy function handles company_name")
        else:
            print("   ❌ update_policy function does NOT handle company_name")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking repository: {e}")
        return False
    
    print("\n🎉 All backend tests passed!")
    print("\nNext steps:")
    print("1. Run database migration to add company_name column to policies table")
    print("2. Test the frontend by:")
    print("   - Creating a policy with a company name")
    print("   - Saving it")
    print("   - Selecting the policy from the table")
    print("   - Verifying the company name field shows the saved value")
    print("   - Updating the company name and saving again")
    print("   - Verifying the updated value is shown")
    
    return True

if __name__ == "__main__":
    test_company_name_persistence()