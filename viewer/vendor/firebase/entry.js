export { initializeApp } from "firebase/app";
export { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged, browserLocalPersistence, setPersistence } from "firebase/auth";
export { getFirestore, doc, getDoc, setDoc, addDoc, collection, getDocs, serverTimestamp } from "firebase/firestore/lite";
