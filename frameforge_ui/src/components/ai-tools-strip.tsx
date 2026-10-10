import adobe from '@/assets/ai-logo-adobe-original.svg.asset.json';
import claude from '@/assets/ai-logo-claude-original.svg.asset.json';
import openai from '@/assets/ai-logo-openai-original.svg.asset.json';
import gemini from '@/assets/ai-logo-gemini-original.svg.asset.json';
import elevenlabs from '@/assets/ai-logo-elevenlabs-original.svg.asset.json';
import kling from '@/assets/ai-logo-kling-original.svg.asset.json';
import suno from '@/assets/ai-logo-suno-original.svg.asset.json';
import capcut from '@/assets/ai-logo-capcut-original.svg.asset.json';

const tools = [
  { name: 'Adobe', image: adobe, href: 'https://www.adobe.com/' },
  { name: 'Claude', image: claude, href: 'https://claude.ai/' },
  { name: 'OpenAI', image: openai, href: 'https://openai.com/' },
  { name: 'Gemini', image: gemini, href: 'https://gemini.google.com/' },
  { name: 'ElevenLabs', image: elevenlabs, href: 'https://elevenlabs.io/' },
  { name: 'Kling', image: kling, href: 'https://klingai.com/' },
  { name: 'Suno', image: suno, href: 'https://suno.com/' },
  { name: 'CapCut', image: capcut, href: 'https://www.capcut.com/' },
];

export function AiToolsStrip() {
  return (
    <div className="ai-tools-strip" role="region" aria-label="AI filmmaking tools">
      <div className="ai-tools-track">
        {[0, 1].map(copy => (
          <div className="ai-tools-group" key={copy} aria-hidden={copy === 1 ? true : undefined}>
            {tools.map(tool => (
              <a key={tool.name} className="ai-tool-logo" href={tool.href} target="_blank" rel="noreferrer" aria-label={tool.name} tabIndex={copy === 1 ? -1 : 0}>
                <img src={tool.image.url} alt="" width="48" height="48" />
                <span className="ai-tool-label">{tool.name}</span>
              </a>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}