"""
Test Address Reputation Database
"""
import pytest
from services.security import ReputationDatabase


def test_reputation_initialization():
    """Test reputation database initializes"""
    rep_db = ReputationDatabase()
    assert rep_db is not None
    assert rep_db.graph is not None
    print("✅ Reputation database initialized")


def test_add_known_phisher():
    """Test adding known phisher address"""
    rep_db = ReputationDatabase()
    
    phisher_address = "0xDeadBeef1234567890123456789012345678DeaD"
    rep_db.add_address(phisher_address, "phisher", {
        "victim_count": 43,
        "total_stolen_usd": 450000
    })
    
    assert phisher_address in rep_db.known_phishers
    print(f"✅ Added phisher: {phisher_address}")


def test_risk_score_calculation():
    """Test risk score calculation"""
    rep_db = ReputationDatabase()
    
    # Add known phisher
    phisher = "0xPhisher123456789012345678901234567890123"
    rep_db.add_address(phisher, "phisher")
    
    # Check risk score
    risk = rep_db.get_risk_score(phisher)
    
    assert "risk_score" in risk
    assert risk["risk_score"] >= 90  # Known phisher should be high risk
    assert "phishing" in risk["labels"] or "wallet_drainer" in risk["labels"]
    
    print(f"✅ Phisher risk score: {risk['risk_score']}/100")
    print(f"   Labels: {risk['labels']}")


def test_unknown_address_risk():
    """Test risk score for unknown address"""
    rep_db = ReputationDatabase()
    
    unknown_address = "0x0000000000000000000000000000000000000001"
    risk = rep_db.get_risk_score(unknown_address)
    
    assert "risk_score" in risk
    assert risk["risk_score"] <= 60  # Unknown should be medium or low
    
    print(f"✅ Unknown address risk: {risk['risk_score']}/100")


if __name__ == "__main__":
    print("\n🧪 Running Reputation Database Tests\n")
    test_reputation_initialization()
    test_add_known_phisher()
    test_risk_score_calculation()
    test_unknown_address_risk()
    print("\n✅ All reputation tests passed!")

