import { useState } from 'react';
import { ShieldCheck, Lock, ScanEye, ScrollText, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { acceptTermsAgreement, useTermsAgreement } from '@/lib/terms-agreement';

interface EscrowTermsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Where to navigate once the user has agreed (handled by parent). */
  onAgreed?: () => void;
  /** Signed-in user's email, recorded in the agreement audit log. */
  userEmail?: string | undefined;
}

/**
 * Escrow & Confidentiality Terms & Conditions onboarding step.
 * Styled to AiGrid's editorial design system: square corners, black CTAs,
 * monospace eyebrow labels, strict black-and-white hierarchy.
 */
export function EscrowTermsDialog({ open, onOpenChange, onAgreed, userEmail }: EscrowTermsDialogProps) {
  const agreement = useTermsAgreement();
  const [agreed, setAgreed] = useState<boolean>(Boolean(agreement));
  const [submitting, setSubmitting] = useState(false);

  function handleProceed() {
    if (!agreed) return;
    setSubmitting(true);
    acceptTermsAgreement(userEmail);
    setSubmitting(false);
    onOpenChange(false);
    if (onAgreed) onAgreed();
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="escrow-terms-dialog" style={{ padding: 0 }}>
        <div className="escrow-terms__body">

          {/* Eyebrow + title block — matches home/hero pattern */}
          <p className="escrow-terms__eyebrow">
            <i /> ESCROW &amp; CONFIDENTIALITY · V1.0
          </p>
          <DialogTitle className="escrow-terms__title">
            Agree to protect<br />your deal
          </DialogTitle>
          <DialogDescription className="escrow-terms__description">
            Before you enter secure chat or finalize a deal, review the platform safety rules.
          </DialogDescription>

          {/* CLEAR TERMS BOX — scrollable */}
          <div className="escrow-terms__scroll" role="region" aria-label="Escrow and confidentiality terms" tabIndex={0}>
            <section>
              <h4>
                <Lock size={14} /> ESCROW SAFETY
              </h4>
              <p>
                All project payments are held in platform escrow. Funds locked in escrow are
                released only when agreed milestones are approved. Creators receive an upfront
                compute allocation (30%) for GPU resources; the remaining balance (70%) unlocks
                after final delivery review.
              </p>
            </section>

            <section>
              <h4>
                <ScanEye size={14} /> CONFIDENTIAL BRAND MODE
              </h4>
              <p>
                During bidding and collaboration, creator and brand identities stay masked behind
                platform-issued pseudonyms. Secure chat is monitored for policy compliance.
              </p>
            </section>

            <section>
              <h4>
                <AlertTriangle size={14} /> NO DIRECT CONTACT / OFF-PLATFORM SHARING
              </h4>
              <p>
                Exchanging phone numbers, social handles, emails, or UPI IDs in chat is strictly
                prohibited. Violations are intercepted automatically and may suspend the account.
                All payments and communication must stay on the platform.
              </p>
            </section>

            <section>
              <h4>
                <ScrollText size={14} /> DISPUTE &amp; REFUND CLAUSE
              </h4>
              <p>
                In case of non-delivery, severe delay, or quality dispute, funds remain securely
                held in platform escrow until our moderation team resolves the issue, ensuring
                fair refunds where applicable.
              </p>
            </section>
          </div>

          {/* INTERACTIVE CHECKBOX — editorial row, not a card */}
          <label className="escrow-terms__agree" htmlFor="escrow-terms-agree">
            <Checkbox
              id="escrow-terms-agree"
              checked={agreed}
              onCheckedChange={(val) => setAgreed(val === true)}
              aria-describedby="escrow-terms-agree-label"
            />
            <span>
              I AGREE TO THE ESCROW TERMS, PRIVACY POLICIES, AND SECURE CHAT GUIDELINES.
            </span>
          </label>

          <div className="escrow-terms__actions">
            <Button variant="outline" className="escrow-terms__close" onClick={() => onOpenChange(false)}>
              Close
            </Button>
            <Button
              className="escrow-terms__proceed"
              onClick={handleProceed}
              disabled={!agreed || submitting}
            >
              <ShieldCheck size={14} />
              Proceed to Secure Deal / Chat
            </Button>
          </div>

          {agreement && (
            <p className="escrow-terms__footnote">
              AGREEMENT RECORDED · {agreement.acceptedAt.slice(0, 10)} · V{agreement.termsVersion.toUpperCase()}
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
