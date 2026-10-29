import type {AuditOut} from './audit.js';

// Main's final SAM records: retain the wall's entire catalog, with these three
// examples providing an entry point into each outcome.
export const openingExampleKeys=['real_own_2','generated_meta_clip4','generated_meta_clip2'] as const;
export const comparisonKeys=[openingExampleKeys[0],openingExampleKeys[1]] as const;

export function savedOutcomeCaption(audit:Pick<AuditOut,'verdict'>){
 return {
  consistent:'This saved motion is consistent with the assumed model.',
  inconsistent:'This saved motion is inconsistent with the assumed model; the cause is not established.',
  insufficient_data:'The saved evidence is insufficient to judge consistency with the assumed model. Review the recorded reasons.',
 }[audit.verdict];
}
