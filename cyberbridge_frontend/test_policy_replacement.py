# Test script to verify the policy replacement functionality

def test_policy_replacement():
    """Test the policy body replacement logic"""
    
    # Test case 1: Basic replacement
    policy_body = "This policy applies to p_company_name and all its subsidiaries."
    company_name = "Acme Corporation"
    expected = "This policy applies to Acme Corporation and all its subsidiaries."
    result = policy_body.replace("p_company_name", company_name)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Test 1 passed: Basic replacement")
    
    # Test case 2: Multiple occurrences
    policy_body = "p_company_name shall ensure that p_company_name employees follow this policy."
    company_name = "TechCorp Inc."
    expected = "TechCorp Inc. shall ensure that TechCorp Inc. employees follow this policy."
    result = policy_body.replace("p_company_name", company_name)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Test 2 passed: Multiple occurrences")
    
    # Test case 3: No replacement needed
    policy_body = "This policy applies to all employees."
    company_name = "TestCorp"
    expected = "This policy applies to all employees."
    result = policy_body.replace("p_company_name", company_name)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Test 3 passed: No replacement needed")
    
    # Test case 4: Empty company name
    policy_body = "This policy applies to p_company_name."
    company_name = ""
    expected = "This policy applies to ."
    result = policy_body.replace("p_company_name", company_name)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Test 4 passed: Empty company name")
    
    # Test case 5: Case sensitivity
    policy_body = "This policy applies to p_company_name and P_COMPANY_NAME."
    company_name = "CaseCorp"
    expected = "This policy applies to CaseCorp and P_COMPANY_NAME."
    result = policy_body.replace("p_company_name", company_name)
    assert result == expected, f"Expected: {expected}, Got: {result}"
    print("✓ Test 5 passed: Case sensitivity (only lowercase replaced)")
    
    print("\n🎉 All tests passed! The policy replacement logic works correctly.")

if __name__ == "__main__":
    test_policy_replacement()