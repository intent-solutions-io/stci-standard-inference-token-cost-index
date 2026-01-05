// Firebase for inferencepriceindex.com
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.7.0/firebase-app.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/12.7.0/firebase-analytics.js";
import { getFirestore, doc, setDoc, collection, addDoc, serverTimestamp } from "https://www.gstatic.com/firebasejs/12.7.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyBk3yt04695pb2tdJAR5gT54bCgIqR9dnE",
  authDomain: "stci-production.firebaseapp.com",
  projectId: "stci-production",
  storageBucket: "stci-production.firebasestorage.app",
  messagingSenderId: "303527277450",
  appId: "1:303527277450:web:0908ffbdd70d52aa034e73",
  measurementId: "G-R3DW0MX0XZ"
};

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const db = getFirestore(app);

// Expose Firestore for non-module scripts
window.firebaseDb = { db, doc, setDoc, collection, addDoc, serverTimestamp };
