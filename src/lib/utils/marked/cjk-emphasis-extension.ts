import { marked } from 'marked';

const CJK_EDGE_REGEX =
	/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Hangul}]/u;
const RELAXED_STRONG_REGEX = /^(\*\*|__)(?=\S)([\s\S]*?\S)\1(?!\1)/u;
const RELAXED_EM_REGEX = /^(\*|_)(?=\S)([\s\S]*?\S)\1(?!\1)/u;

function hasCjkEdge(text: string) {
	if (!text) return false;
	return CJK_EDGE_REGEX.test(text[0]) || CJK_EDGE_REGEX.test(text[text.length - 1]);
}

function buildToken(this: any, match: RegExpExecArray, type: 'strong' | 'em') {
	return {
		type,
		raw: match[0],
		text: match[2],
		tokens: this.lexer.inlineTokens(match[2])
	};
}

export default function cjkEmphasisExtension() {
	return {
		name: 'cjk-emphasis',
		level: 'inline' as const,
		tokenizer: {
			strong(this: any, src: string) {
				const base = marked.Tokenizer.prototype.strong.call(this, src);
				if (base) return base;

				const match = RELAXED_STRONG_REGEX.exec(src);
				if (!match || !hasCjkEdge(match[2])) return;

				return buildToken.call(this, match, 'strong');
			},
			em(this: any, src: string) {
				const base = marked.Tokenizer.prototype.em.call(this, src);
				if (base) return base;

				const match = RELAXED_EM_REGEX.exec(src);
				if (!match || !hasCjkEdge(match[2])) return;

				return buildToken.call(this, match, 'em');
			}
		}
	};
}
