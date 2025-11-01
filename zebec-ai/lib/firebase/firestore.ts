import {
  collection,
  doc,
  getDoc,
  getDocs,
  setDoc,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  Timestamp,
  DocumentData,
  QueryConstraint,
} from 'firebase/firestore';
import { db } from './config';
import { UserProfile, Content, ConnectedPlatform } from '@/types';

// Collection references
export const COLLECTIONS = {
  USERS: 'users',
  CONTENT: 'content',
  ANALYTICS: 'analytics',
  NOTIFICATIONS: 'notifications',
  SCHEDULED_POSTS: 'scheduled_posts',
};

// User Profile Operations
export const getUserProfile = async (uid: string): Promise<UserProfile | null> => {
  try {
    const docRef = doc(db, COLLECTIONS.USERS, uid);
    const docSnap = await getDoc(docRef);
    
    if (docSnap.exists()) {
      return docSnap.data() as UserProfile;
    }
    return null;
  } catch (error) {
    console.error('Error getting user profile:', error);
    throw error;
  }
};

export const createUserProfile = async (uid: string, data: Partial<UserProfile>): Promise<void> => {
  try {
    const docRef = doc(db, COLLECTIONS.USERS, uid);
    const timestamp = new Date().toISOString();
    
    await setDoc(docRef, {
      uid,
      ...data,
      createdAt: timestamp,
      updatedAt: timestamp,
    });
  } catch (error) {
    console.error('Error creating user profile:', error);
    throw error;
  }
};

export const updateUserProfile = async (uid: string, data: Partial<UserProfile>): Promise<void> => {
  try {
    const docRef = doc(db, COLLECTIONS.USERS, uid);
    await updateDoc(docRef, {
      ...data,
      updatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

// Content Operations
export const createContent = async (content: Omit<Content, 'id'>): Promise<string> => {
  try {
    const docRef = doc(collection(db, COLLECTIONS.CONTENT));
    const contentWithId = {
      ...content,
      id: docRef.id,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    
    await setDoc(docRef, contentWithId);
    return docRef.id;
  } catch (error) {
    console.error('Error creating content:', error);
    throw error;
  }
};

export const getUserContent = async (userId: string, limitCount = 50): Promise<Content[]> => {
  try {
    const q = query(
      collection(db, COLLECTIONS.CONTENT),
      where('userId', '==', userId),
      orderBy('createdAt', 'desc'),
      limit(limitCount)
    );
    
    const querySnapshot = await getDocs(q);
    return querySnapshot.docs.map(doc => doc.data() as Content);
  } catch (error) {
    console.error('Error getting user content:', error);
    throw error;
  }
};

export const updateContent = async (contentId: string, data: Partial<Content>): Promise<void> => {
  try {
    const docRef = doc(db, COLLECTIONS.CONTENT, contentId);
    await updateDoc(docRef, {
      ...data,
      updatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error updating content:', error);
    throw error;
  }
};

export const deleteContent = async (contentId: string): Promise<void> => {
  try {
    const docRef = doc(db, COLLECTIONS.CONTENT, contentId);
    await deleteDoc(docRef);
  } catch (error) {
    console.error('Error deleting content:', error);
    throw error;
  }
};

// Real-time listeners
export const subscribeToUserProfile = (
  uid: string,
  callback: (profile: UserProfile | null) => void
) => {
  const docRef = doc(db, COLLECTIONS.USERS, uid);
  
  return onSnapshot(docRef, (doc) => {
    if (doc.exists()) {
      callback(doc.data() as UserProfile);
    } else {
      callback(null);
    }
  }, (error) => {
    console.error('Error in user profile subscription:', error);
    callback(null);
  });
};

export const subscribeToUserContent = (
  userId: string,
  callback: (content: Content[]) => void
) => {
  const q = query(
    collection(db, COLLECTIONS.CONTENT),
    where('userId', '==', userId),
    orderBy('createdAt', 'desc'),
    limit(50)
  );
  
  return onSnapshot(q, (querySnapshot) => {
    const content = querySnapshot.docs.map(doc => doc.data() as Content);
    callback(content);
  }, (error) => {
    console.error('Error in content subscription:', error);
    callback([]);
  });
};

// Platform Operations
export const addConnectedPlatform = async (
  uid: string,
  platform: ConnectedPlatform
): Promise<void> => {
  try {
    const profile = await getUserProfile(uid);
    if (!profile) throw new Error('User profile not found');
    
    const platforms = profile.connectedPlatforms || [];
    const existingIndex = platforms.findIndex(p => p.id === platform.id);
    
    if (existingIndex >= 0) {
      platforms[existingIndex] = platform;
    } else {
      platforms.push(platform);
    }
    
    await updateUserProfile(uid, { connectedPlatforms: platforms });
  } catch (error) {
    console.error('Error adding connected platform:', error);
    throw error;
  }
};

export const removeConnectedPlatform = async (
  uid: string,
  platformId: string
): Promise<void> => {
  try {
    const profile = await getUserProfile(uid);
    if (!profile) throw new Error('User profile not found');
    
    const platforms = profile.connectedPlatforms.filter(p => p.id !== platformId);
    await updateUserProfile(uid, { connectedPlatforms: platforms });
  } catch (error) {
    console.error('Error removing connected platform:', error);
    throw error;
  }
};
