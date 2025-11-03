"""
Verification Pipeline - Verifies scraped data with confidence scores
"""
from typing import Dict, List
from loguru import logger


class DataVerifier:
    """
    Verification pipeline for scraped data
    Calculates confidence scores and flags suspicious data
    """
    
    def __init__(self):
        self.verification_logs: List[Dict] = []
    
    def verify_supplier(self, supplier_data: Dict, search_results: List[Dict]) -> Dict:
        """
        Verify supplier data quality and legitimacy
        
        Args:
            supplier_data: Supplier information to verify
            search_results: Additional search results for cross-referencing
        
        Returns:
            Verification result with confidence score
        """
        verification = {
            "confidence": 0.0,
            "sources_checked": len(search_results),
            "legitimacy_indicators": [],
            "red_flags": [],
            "cross_references": [],
            "quality_score": 0.0
        }
        
        # Check 1: Completeness
        completeness_score = self._check_completeness(supplier_data)
        
        # Check 2: Contact information
        contact_score = self._check_contact_info(supplier_data)
        
        # Check 3: Cross-references
        cross_ref_score = self._check_cross_references(supplier_data, search_results)
        
        # Check 4: Red flags
        red_flag_count = self._check_red_flags(search_results)
        
        # Calculate overall confidence
        base_confidence = 0.5
        confidence = base_confidence
        confidence += completeness_score * 0.2
        confidence += contact_score * 0.15
        confidence += cross_ref_score * 0.15
        confidence -= red_flag_count * 0.2
        
        verification["confidence"] = max(0.0, min(1.0, confidence))
        verification["quality_score"] = (completeness_score + contact_score) / 2
        
        # Add legitimacy indicators
        if supplier_data.get("contact", {}).get("phone"):
            verification["legitimacy_indicators"].append("Phone number provided")
        if supplier_data.get("contact", {}).get("email"):
            verification["legitimacy_indicators"].append("Email provided")
        if supplier_data.get("contact", {}).get("website"):
            verification["legitimacy_indicators"].append("Website available")
        if supplier_data.get("location", {}).get("city"):
            verification["legitimacy_indicators"].append("Location specified")
        
        # Log verification
        self.verification_logs.append({
            "type": "supplier",
            "name": supplier_data.get("name", "Unknown"),
            "confidence": verification["confidence"],
            "timestamp": self._get_timestamp()
        })
        
        logger.info(f"Verified supplier: {supplier_data.get('name')} (confidence: {verification['confidence']:.2f})")
        
        return verification
    
    def verify_event(self, event_data: Dict, search_results: List[Dict]) -> Dict:
        """
        Verify event data quality
        
        Args:
            event_data: Event information
            search_results: Additional search results
        
        Returns:
            Verification result
        """
        verification = {
            "confidence": 0.0,
            "sources_checked": len(search_results),
            "legitimacy_indicators": [],
            "red_flags": []
        }
        
        # Check for required fields
        required_fields = ["name", "date", "location"]
        completeness = sum(1 for field in required_fields if event_data.get(field)) / len(required_fields)
        
        # Check contact info
        has_contact = bool(event_data.get("contact", {}).get("website") or 
                          event_data.get("organizer"))
        
        confidence = 0.4  # Base
        confidence += completeness * 0.3
        confidence += (0.2 if has_contact else 0.0)
        
        # Check for multiple sources mentioning the event
        if len(search_results) > 1:
            confidence += 0.1
        
        verification["confidence"] = max(0.0, min(1.0, confidence))
        
        if event_data.get("contact"):
            verification["legitimacy_indicators"].append("Contact information available")
        if event_data.get("organizer"):
            verification["legitimacy_indicators"].append("Organizer specified")
        
        return verification
    
    def _check_completeness(self, data: Dict) -> float:
        """Check data completeness (0-1 score)"""
        required_fields = ["name"]
        optional_fields = ["contact", "location", "products"]
        
        score = 0.0
        
        # Required fields
        required_present = sum(1 for field in required_fields if data.get(field))
        score += (required_present / len(required_fields)) * 0.5
        
        # Optional fields
        optional_present = sum(1 for field in optional_fields if data.get(field))
        score += (optional_present / len(optional_fields)) * 0.5
        
        return score
    
    def _check_contact_info(self, data: Dict) -> float:
        """Check contact information quality (0-1 score)"""
        contact = data.get("contact", {})
        
        score = 0.0
        if contact.get("phone"):
            score += 0.3
        if contact.get("email"):
            score += 0.3
        if contact.get("website"):
            score += 0.4
        
        return score
    
    def _check_cross_references(self, data: Dict, search_results: List[Dict]) -> float:
        """Check cross-references in search results (0-1 score)"""
        name = data.get("name", "").lower()
        
        if not name:
            return 0.0
        
        mentions = sum(1 for result in search_results 
                      if name in result.get("title", "").lower() or 
                      name in result.get("snippet", "").lower())
        
        # More mentions = higher score (capped at 1.0)
        return min(1.0, mentions * 0.2)
    
    def _check_red_flags(self, search_results: List[Dict]) -> int:
        """Count red flags in search results"""
        red_flag_keywords = ["scam", "fraud", "fake", "complaint", "beware", "warning"]
        red_flag_count = 0
        
        for result in search_results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()
            
            for keyword in red_flag_keywords:
                if keyword in snippet or keyword in title:
                    red_flag_count += 1
                    break  # Count each result only once
        
        if red_flag_count > 0:
            logger.warning(f"Found {red_flag_count} red flag(s)")
        
        return red_flag_count
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_verification_logs(self) -> List[Dict]:
        """Get all verification logs"""
        return self.verification_logs

