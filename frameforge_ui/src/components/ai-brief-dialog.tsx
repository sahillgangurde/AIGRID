import { useState } from 'react';
import { Sparkles, ArrowRight, CheckCircle2, AlertCircle, RefreshCw, Send, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';

interface AIBriefDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBriefCreated?: (brief: any) => void;
}

export function AIBriefDialog({ open, onOpenChange, onBriefCreated }: AIBriefDialogProps) {
  const [rawIdea, setRawIdea] = useState('');
  const [brandName, setBrandName] = useState('Brand Studio');
  const [budget, setBudgetTarget] = useState('3500');
  const [currency, setCurrency] = useState('USD');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [structured, setStructured] = useState<any>(null);
  const [postedSuccess, setPostedSuccess] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  function resetState() {
    setRawIdea('');
    setStructured(null);
    setPostedSuccess(null);
    setError(null);
    setIsGenerating(false);
    setIsPosting(false);
  }

  async function handleAIGenerate() {
    if (!rawIdea.trim()) return;
    setIsGenerating(true);
    setError(null);
    try {
      const res = await fetch('/api/briefs/ai-generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_idea: rawIdea.trim(),
          brand_name: brandName.trim() || 'Brand Studio',
          budget_target: parseFloat(budget) || 3500,
          currency: currency
        })
      });
      if (!res.ok) throw new Error('AI generation service error');
      const data = await res.json();
      setStructured(data);
    } catch (err: any) {
      setError('Could not connect to AI generation engine. Using fallback preview.');
      // Heuristic fallback preview if backend is unreachable
      setStructured({
        title: `${brandName} • Commercial Video Campaign`,
        objective: rawIdea,
        content_type: 'Social Video Commercial',
        style: 'High-Energy Kinetic Cinema',
        format_aspect_ratio: '9:16 (Vertical Reels/TikTok)',
        commercial_use: 'Full Commercial Buyout with C2PA Provenance',
        tools_recommended: ['Runway Gen-3', 'ComfyUI', 'FLUX.1 Dev'],
        required_skills: ['Temporal Consistency', 'Motion Control'],
        budget_usd: parseFloat(budget) || 3500,
        timeline_days: 7,
        clarifying_questions: ['Do you have raw footage or should 100% synthetic scenes be generated?']
      });
    } finally {
      setIsGenerating(false);
    }
  }

  async function handlePostBrief() {
    if (!structured) return;
    setIsPosting(true);
    setError(null);
    try {
      const payload = {
        title: structured.title,
        brand_name: brandName || 'Brand Studio',
        objective: structured.objective,
        description: rawIdea,
        content_type: structured.content_type,
        style: structured.style,
        format_aspect_ratio: structured.format_aspect_ratio,
        commercial_use: structured.commercial_use,
        tools_recommended: structured.tools_recommended,
        required_skills: structured.required_skills,
        budget_usd: structured.budget_usd || 3500,
        currency: currency,
        timeline_days: structured.timeline_days || 7,
        confidentiality: 'public'
      };

      const res = await fetch('/api/briefs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Failed to save brief');
      const data = await res.json();
      setPostedSuccess(data.brief || data);
      if (onBriefCreated) onBriefCreated(data.brief || data);
    } catch (err: any) {
      setError('Failed to persist brief to database. Please try again.');
    } finally {
      setIsPosting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(val) => { onOpenChange(val); if (!val) resetState(); }}>
      <DialogContent className="account-dialog max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="account-dialog-body" style={{ textAlign: 'left', padding: '24px 28px' }}>
          
          {/* Header — AiGrid editorial pattern */}
          <p style={{ font: '10px monospace', textTransform: 'uppercase', letterSpacing: 2, display: 'flex', gap: 10, alignItems: 'center', margin: 0, marginBottom: 14, color: 'var(--muted-foreground)' }}>
            <i style={{ width: 6, height: 6, background: 'var(--highlight)', display: 'inline-block' }} /> AI BRIEF ENGINE
          </p>

          <DialogTitle style={{ color: 'var(--foreground)' }}>
            {postedSuccess ? 'Brief Published & Creators Matched!' : (structured ? 'Review AI-Structured Brief' : 'Describe Your Creative Vision')}
          </DialogTitle>
          
          <DialogDescription style={{ fontSize: '0.9rem', color: 'var(--foreground)', marginTop: 6, marginBottom: 20 }}>
            {postedSuccess ? 'Your project is now open for matched creators with verified escrow protection.' : 
             structured ? 'Review the extracted deliverables, timeline, and recommended tools below.' :
             'Type your raw ideas, rough thoughts, or campaign goals. Our AI engine will structure it into a production brief.'}
          </DialogDescription>

          {error && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', padding: '10px 14px', borderRadius: 8, color: '#991B1B', fontSize: '0.84rem', marginBottom: 16, display: 'flex', gap: 8, alignItems: 'center' }}>
              <AlertCircle size={16} /> {error}
            </div>
          )}

          {/* SUCCESS SCREEN */}
          {postedSuccess ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div style={{ background: '#F0FDF4', border: '1px solid #86EFAC', borderRadius: 12, padding: '16px 20px', color: '#166534' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: '1rem', marginBottom: 6 }}>
                  <CheckCircle2 size={18} color="#16A34A" /> Brief Saved to Persistent Database
                </div>
                <p style={{ fontSize: '0.86rem', color: '#15803D' }}>
                  <strong>{postedSuccess.title}</strong> is active. Top matched creators have been notified.
                </p>
              </div>

              <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 18px' }}>
                <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: '#374151', marginBottom: 8 }}>
                  Smart Escrow Protection Active
                </h4>
                <div style={{ fontSize: '0.82rem', color: '#6B7280', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <span>🔒 Upfront compute cost protected by smart escrow.</span>
                  <span>🛡️ C2PA cryptographically signed verification upon delivery.</span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
                <Button className="pill" onClick={() => { onOpenChange(false); resetState(); }}>
                  Done <ArrowRight size={14} style={{ marginLeft: 6 }} />
                </Button>
              </div>
            </div>
          ) : structured ? (
            /* STRUCTURED PREVIEW & CONFIRMATION */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              
              <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 18px' }}>
                <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#6B7280', fontWeight: 700 }}>
                  Structured Campaign Title
                </div>
                <input 
                  type="text" 
                  value={structured.title} 
                  onChange={e => setStructured({ ...structured, title: e.target.value })}
                  style={{ width: '100%', marginTop: 4, padding: '8px 12px', border: '1px solid #D1D5DB', borderRadius: 8, fontSize: '0.95rem', fontWeight: 600 }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 14px' }}>
                  <span style={{ fontSize: '0.74rem', color: '#6B7280', fontWeight: 700, textTransform: 'uppercase' }}>Format & Aspect Ratio</span>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#1F2937', marginTop: 2 }}>{structured.format_aspect_ratio || '9:16 Vertical'}</div>
                </div>
                <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 14px' }}>
                  <span style={{ fontSize: '0.74rem', color: '#6B7280', fontWeight: 700, textTransform: 'uppercase' }}>Estimated Budget</span>
                  <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#10B981', marginTop: 2 }}>${structured.budget_usd || budget} USD</div>
                </div>
              </div>

              <div style={{ background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 10, padding: '12px 14px' }}>
                <span style={{ fontSize: '0.74rem', color: '#6B7280', fontWeight: 700, textTransform: 'uppercase' }}>Recommended AI Tools & Skills</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
                  {(structured.tools_recommended || ['FLUX.1 Dev', 'ComfyUI', 'Runway Gen-3']).map((tool: string, idx: number) => (
                    <span key={idx} style={{ background: '#E0E7FF', color: '#3730A3', padding: '4px 10px', borderRadius: 999, fontSize: '0.76rem', fontWeight: 600 }}>
                      {tool}
                    </span>
                  ))}
                  {(structured.required_skills || []).map((sk: string, idx: number) => (
                    <span key={idx} style={{ background: '#FEF3C7', color: '#92400E', padding: '4px 10px', borderRadius: 999, fontSize: '0.76rem', fontWeight: 600 }}>
                      {sk}
                    </span>
                  ))}
                </div>
              </div>

              {structured.missing_details_questions && structured.missing_details_questions.length > 0 && (
                <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: 10, padding: '12px 14px' }}>
                  <span style={{ fontSize: '0.75rem', color: '#1E40AF', fontWeight: 700, textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Sparkles size={13} /> AI Clarifying Questions
                  </span>
                  <ul style={{ margin: '6px 0 0 18px', fontSize: '0.82rem', color: '#1E3A8A', lineHeight: 1.5 }}>
                    {structured.missing_details_questions.map((q: string, idx: number) => (
                      <li key={idx}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 10 }}>
                <Button variant="ghost" onClick={() => setStructured(null)} style={{ fontSize: '0.84rem' }}>
                  <RefreshCw size={14} style={{ marginRight: 6 }} /> Edit Raw Concept
                </Button>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                  <Button className="pill" onClick={handlePostBrief} disabled={isPosting}>
                    {isPosting ? 'Publishing...' : 'Confirm & Post Brief'} <Send size={13} style={{ marginLeft: 6 }} />
                  </Button>
                  {/* CTA now inherits the default black pill styling */}
                </div>
              </div>
            </div>
          ) : (
            /* RAW INPUT STAGE */
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#374151', marginBottom: 4 }}>
                  Brand or Organization
                </label>
                <input 
                  type="text"
                  placeholder="e.g. Puma Innovation Lab, Nike ACG, Studio Acme"
                  value={brandName}
                  onChange={e => setBrandName(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', border: '1px solid #D1D5DB', borderRadius: 8, fontSize: '0.9rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#374151', marginBottom: 4 }}>
                  What are you creating? (Rough prompt or full concept)
                </label>
                <textarea 
                  rows={4}
                  placeholder="Describe your vision in plain English... e.g. We need a 15-second high-energy cyberpunk commercial for futuristic sneakers with glowing neon sole physics and slow-mo liquid splashes for an Instagram Reel launch."
                  value={rawIdea}
                  onChange={e => setRawIdea(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', border: '1px solid #D1D5DB', borderRadius: 8, fontSize: '0.9rem', lineHeight: 1.5 }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#374151', marginBottom: 4 }}>
                    Estimated Target Budget
                  </label>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <select 
                      value={currency} 
                      onChange={e => setCurrency(e.target.value)}
                      style={{ padding: '8px 10px', border: '1px solid #D1D5DB', borderRadius: 8, fontSize: '0.85rem' }}
                    >
                      <option value="USD">USD ($)</option>
                      <option value="INR">INR (₹)</option>
                    </select>
                    <input 
                      type="number"
                      value={budget}
                      onChange={e => setBudgetTarget(e.target.value)}
                      style={{ flex: 1, padding: '8px 10px', border: '1px solid #D1D5DB', borderRadius: 8, fontSize: '0.85rem' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 700, color: '#374151', marginBottom: 4 }}>
                    Identity Protection
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 12px', background: '#F3F4F6', borderRadius: 8, fontSize: '0.82rem', color: '#4B5563' }}>
                    <Lock size={14} color="#059669" /> Masked Brand Escrow Active
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
                <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                <Button 
                  className="pill" 
                  onClick={handleAIGenerate} 
                  disabled={isGenerating || !rawIdea.trim()}
                >
                  {isGenerating ? (
                    <>
                      <Sparkles size={14} className="animate-spin" style={{ marginRight: 6 }} /> 
                      Structuring with AI...
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} style={{ marginRight: 6 }} /> 
                      Auto-Structure with AI
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

        </div>
      </DialogContent>
    </Dialog>
  );
}
