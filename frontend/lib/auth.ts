"use client";

import { useEffect, useState } from "react";
import {
  browserLocalPersistence,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  type User
} from "firebase/auth";

import { firebaseAuth } from "@/lib/firebase";

export type FirebaseSession = {
  uid: string;
  email: string | null;
  idToken: string;
};

export type FirebaseAuthState = {
  user: User | null;
  ready: boolean;
};

export async function loginWithFirebase(email: string, password: string): Promise<FirebaseSession> {
  if (!firebaseAuth) {
    throw new Error("Firebase web authentication is not configured.");
  }

  await setPersistence(firebaseAuth, browserLocalPersistence);
  const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);

  return {
    uid: credential.user.uid,
    email: credential.user.email,
    idToken: await credential.user.getIdToken()
  };
}

export async function getCurrentFirebaseToken(forceRefresh = false): Promise<string | undefined> {
  const user = firebaseAuth?.currentUser;
  if (!user) {
    return undefined;
  }

  return user.getIdToken(forceRefresh);
}

export function listenToFirebaseUser(callback: (user: User | null) => void): () => void {
  if (!firebaseAuth) {
    callback(null);
    return () => undefined;
  }

  return onAuthStateChanged(firebaseAuth, callback);
}

export async function logoutFirebase(): Promise<void> {
  if (!firebaseAuth) {
    return;
  }

  await signOut(firebaseAuth);
}

export function useFirebaseAuthState(): FirebaseAuthState {
  const [user, setUser] = useState<User | null>(firebaseAuth?.currentUser ?? null);
  const [ready, setReady] = useState(!firebaseAuth);

  useEffect(
    () =>
      listenToFirebaseUser((nextUser) => {
        setUser(nextUser);
        setReady(true);
      }),
    []
  );

  return { user, ready };
}
