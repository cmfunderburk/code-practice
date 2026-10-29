import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App';
import { markLaunch, rememberRoutes, restoreLastRoute } from './route';
import { requestPersistence } from './store/persistence';
import { registerServiceWorker } from './sw/register';

const root = document.getElementById('root');
if (!root) throw new Error('missing #root');

async function start(root: HTMLElement): Promise<void> {
  await restoreLastRoute();
  markLaunch();
  rememberRoutes();
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

void start(root);
registerServiceWorker();
void requestPersistence();
