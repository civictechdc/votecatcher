import { type OcrProvider } from '../../types/ocr';

const OPEN_AI: OcrProvider = {
	apiKeyId: 'OPENAI_API_KEY',
	name: 'OpenAI',
	apiKeyDocs: 'https://platform.openai.com/api-keys'
};

const GOOGLE_GEMINI: OcrProvider = {
	apiKeyId: 'GEMINI_API_KEY',
	name: 'Google Gemini',
	apiKeyDocs: 'https://ai.google.dev/gemini-api/docs/api-key#api-keys'
};

const MISTRAL_AI: OcrProvider = {
	apiKeyId: 'MISTRAL_API_KEY',
	name: 'Mistral AI',
	apiKeyDocs: 'https://docs.mistral.ai/getting-started/quickstart'
};

export const OCR_PROVIDER_SELECTION: OcrProvider[] = [OPEN_AI, GOOGLE_GEMINI, MISTRAL_AI];
