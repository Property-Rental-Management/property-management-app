import pytest

from src.controller import UnauthorizedError
from src.controller.companies import CompaniesController
from src.database.models.companies import Company
from tests.controller import Session


# Assuming you have imported the necessary classes and exceptions

@pytest.fixture
def companies_controller():
    return CompaniesController(session_maker=Session)


# Test case for is_company_member method
def test_is_company_member(companies_controller, mocked_session):
    # Test case with a valid user and company IDs
    result = await companies_controller.is_company_member(user_id="user1", company_id="company1",
                                                          session=mocked_session)
    assert result == False


# Test case for get_user_companies method
def test_get_user_companies(companies_controller, mocked_session):
    # Test case with a valid user ID
    result = await companies_controller.get_user_companies(user_id="user1")
    assert isinstance(result, list)
    assert len(result) == 2  # Assuming there are two companies associated with the user

    # Test case with an invalid user ID
    result = await companies_controller.get_user_companies(user_id="invalid_user")
    assert isinstance(result, list)
    assert len(result) == 0  # No companies associated with the invalid user


# Test case for get_company method (Authorized)
def test_get_company_authorized(companies_controller, mocked_session):
    # Test case with a valid company ID and an authorized user
    result = await companies_controller.get_company(company_id="company1", user_id="user1")
    assert isinstance(result, Company)
    assert result.company_id == "company1"

    # Test case with an invalid company ID and an authorized user
    result = companies_controller.get_company(company_id="invalid_company", user_id="user1")
    assert result is None


# Test case for get_company method (Unauthorized)
def test_get_company_unauthorized(companies_controller, mocked_session):
    # Test case with a valid company ID and an unauthorized user
    with pytest.raises(UnauthorizedError) as e:
        companies_controller.get_company(company_id="company1", user_id="unauthorized_user")
    assert str(e.value).casefold() == "You are not authorized to access this company".casefold()

    # Test case with an invalid company ID and an unauthorized user
    with pytest.raises(UnauthorizedError) as e:
        companies_controller.get_company(company_id="invalid_company", user_id="unauthorized_user")
    assert str(e.value).casefold() == "You are not authorized to access this company".casefold()
