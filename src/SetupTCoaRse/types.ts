/**
 * The settings the setup page writes into the block's "Setup TCoaRse"
 * variable. The keys match the ids the block reads in TCoaRsePipeline.py, so
 * anything saved here is picked up as-is; keys left empty fall back to the
 * block variables and then to the TCoaRse configuration.
 *
 * `window.horusVariable` and `window.horus` are already declared globally in
 * src/Setup/components/Setup/types.ts and are not redeclared here.
 */
export type TCoaRseSettings = {
  af3_dir: string;
  chain_map: string;
  not_experimental: boolean;
  energy_threshold: number;
  io_workers: number;
  chunk_size: number;
  pydock_modules: string;
  model: string;
};

/**
 * `window.horus` and `window.horusVariable` are already declared globally in
 * src/Setup/components/Setup/types.ts, as `any`, and are not redeclared here.
 * Horus injects `horusVariable` into the iframe but not `horus`, so the host
 * API is reached through `parent` -- same-origin, since Horus serves the page.
 */
