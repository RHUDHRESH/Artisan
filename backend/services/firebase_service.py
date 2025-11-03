"""
Firebase Service - Optional integration for user data, notifications, and authentication
"""
from typing import Optional, Dict, Any
from loguru import logger
import os


class FirebaseService:
    """
    Firebase integration for user data management
    Optional component - only needed if using Firebase
    """
    
    def __init__(self):
        self.enabled = False
        self.firebase_admin = None
        
        # Check if Firebase credentials are available
        firebase_key = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if firebase_key:
            try:
                import firebase_admin
                from firebase_admin import credentials, firestore
                
                cred = credentials.Certificate(firebase_key)
                firebase_admin.initialize_app(cred)
                
                self.db = firestore.client()
                self.enabled = True
                logger.info("Firebase initialized")
            except ImportError:
                logger.warning("firebase-admin not installed. Firebase features disabled.")
            except Exception as e:
                logger.error(f"Firebase initialization error: {e}")
        else:
            logger.info("Firebase credentials not provided. Using local storage only.")
    
    async def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """
        Save user profile to Firebase
        
        Args:
            user_id: User identifier
            profile: Profile data
        
        Returns:
            Success status
        """
        if not self.enabled:
            logger.debug("Firebase not enabled, skipping save")
            return False
        
        try:
            self.db.collection('users').document(user_id).set(profile)
            logger.info(f"Saved profile for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user profile from Firebase
        
        Args:
            user_id: User identifier
        
        Returns:
            Profile data or None
        """
        if not self.enabled:
            return None
        
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error retrieving profile: {e}")
            return None
    
    async def save_notification(self, user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Save notification for user
        
        Args:
            user_id: User identifier
            notification: Notification data
        
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            self.db.collection('notifications').add({
                'user_id': user_id,
                **notification,
                'timestamp': __import__('datetime').datetime.now().isoformat()
            })
            logger.info(f"Saved notification for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving notification: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Check if Firebase is enabled"""
        return self.enabled

