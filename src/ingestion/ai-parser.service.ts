import { Injectable, Inject } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import OpenAI from 'openai';

const SYSTEM_PROMPT = `Du bist ein Datenextraktor. Extrahiere aus dem folgenden PDF-Text Prüfungsdaten und gib ausschließlich ein JSON-Objekt zurück (kein Markdown, kein Text davor oder danach) das folgendem Schema entspricht:
{
  "beruf": {
    "beschreibung": "<Berufsbezeichnung>",
    "berufNr": [<Nummer als Integer>],
    "pruefungsBereiche": [
      {
        "name": "<Name des Prüfungsbereichs>",
        "aufgaben": [
          {
            "name": "<Name der Aufgabe>",
            "struktur": "<Beschreibung der Struktur>",
            "termin": {
              "datum": "<TT.MM.JJJJ>",
              "uhrzeitvon": "<HH:MM>",
              "uhrzeitbis": "<HH:MM>",
              "dauer": <Minuten als Integer>
            },
            "hilfmittel": "<optional>"
          }
        ]
      }
    ]
  }
}
Antworte NUR mit dem JSON-Objekt.`;

@Injectable()
export class AiParserService {
  private readonly client: OpenAI;

  constructor(@Inject(ConfigService) private readonly config: ConfigService) {
    this.client = new OpenAI({
      apiKey: config.getOrThrow<string>('AI_HUB_API_KEY'),
      baseURL: config.getOrThrow<string>('AI_HUB_BASE_URL'),
    });
  }

  async parse(text: string): Promise<unknown> {
    const response = await this.client.chat.completions.create({
      model: 'claude-sonnet-4-6',
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: text },
      ],
    });

    const content = response.choices[0]?.message?.content ?? '';

    try {
      return JSON.parse(content) as unknown;
    } catch {
      throw new Error(`Failed to parse AI response as JSON: ${content.slice(0, 200)}`);
    }
  }
}
