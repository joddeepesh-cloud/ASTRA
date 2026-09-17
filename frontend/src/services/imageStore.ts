/**
 * ASTRA Persistent IndexedDB Image Store.
 * 
 * Manages original uploaded image Blobs in browser IndexedDB ("ASTRA_IMAGE_STORE").
 * Allows historical observations to reconstruct original user-uploaded images
 * without relying on temporary object URLs or storing large base64 Blobs in localStorage.
 */

const DB_NAME = 'ASTRA_IMAGE_STORE';
const DB_VERSION = 1;
const STORE_NAME = 'images';

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) {
      reject(new Error('IndexedDB is not supported in this environment.'));
      return;
    }

    const request = window.indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = (event: IDBVersionChangeEvent) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = (event: Event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      resolve(db);
    };

    request.onerror = (event: Event) => {
      const err = (event.target as IDBOpenDBRequest).error;
      reject(err || new Error('Failed to open IndexedDB database.'));
    };
  });
}

/**
 * Save an image Blob/File to IndexedDB under a unique imageKey.
 */
export async function saveImageBlob(imageKey: string, blob: Blob | File): Promise<string> {
  try {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put(blob, imageKey);

      request.onsuccess = () => resolve(imageKey);
      request.onerror = () => reject(request.error);
    });
  } catch (err) {
    console.warn('Failed to save image Blob to IndexedDB:', err);
    return imageKey;
  }
}

/**
 * Retrieve an image Blob from IndexedDB by imageKey.
 */
export async function getImageBlob(imageKey: string): Promise<Blob | null> {
  try {
    const db = await openDatabase();
    return new Promise((resolve) => {
      const transaction = db.transaction(STORE_NAME, 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(imageKey);

      request.onsuccess = () => {
        const result = request.result;
        if (result && result instanceof Blob) {
          resolve(result);
        } else {
          resolve(null);
        }
      };

      request.onerror = () => resolve(null);
    });
  } catch (err) {
    console.warn('Failed to retrieve image Blob from IndexedDB:', err);
    return null;
  }
}

/**
 * Delete an image Blob from IndexedDB by imageKey.
 */
export async function deleteImageBlob(imageKey: string): Promise<void> {
  try {
    const db = await openDatabase();
    return new Promise((resolve) => {
      const transaction = db.transaction(STORE_NAME, 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(imageKey);

      request.onsuccess = () => resolve();
      request.onerror = () => resolve();
    });
  } catch (err) {
    console.warn('Failed to delete image Blob from IndexedDB:', err);
  }
}
