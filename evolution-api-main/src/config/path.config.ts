import { join } from 'path';

export const ROOT_DIR = process.cwd();
export const INSTANCE_DIR = process.env.INSTANCE_DIR || process.env.RAILWAY_VOLUME_MOUNT_PATH || '/sessions';
export const SRC_DIR = join(ROOT_DIR, 'src');
export const AUTH_DIR = join(ROOT_DIR, 'store', 'auth');
export const STORE_DIR = join(ROOT_DIR, 'store');
