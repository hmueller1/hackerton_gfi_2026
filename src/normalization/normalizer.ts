import Ajv from 'ajv';
import { BerufDocument } from '../domain/interfaces';

const ajv = new Ajv();

const validate = ajv.compile({
  $schema: 'http://json-schema.org/draft-07/schema#',
  type: 'object',
  properties: {
    beruf: {
      type: 'object',
      properties: {
        beschreibung: { type: 'string' },
        berufNr: { type: 'array', items: { type: 'integer' } },
        pruefungsBereiche: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              name: { type: 'string' },
              aufgaben: {
                type: 'array',
                items: {
                  type: 'object',
                  properties: {
                    name: { type: 'string' },
                    struktur: { type: 'string' },
                    termin: {
                      type: 'object',
                      properties: {
                        datum: { type: 'string' },
                        uhrzeitvon: { type: 'string' },
                        uhrzeitbis: { type: 'string' },
                        dauer: { type: 'integer' },
                      },
                      required: ['datum', 'uhrzeitvon', 'uhrzeitbis', 'dauer'],
                      additionalProperties: false,
                    },
                    hilfmittel: { type: 'string' },
                  },
                  required: ['name', 'struktur', 'termin'],
                  additionalProperties: false,
                },
              },
            },
            required: ['name', 'aufgaben'],
            additionalProperties: false,
          },
        },
      },
      required: ['beschreibung', 'berufNr', 'pruefungsBereiche'],
      additionalProperties: false,
    },
  },
  required: ['beruf'],
  additionalProperties: false,
});

export const normalize = (raw: unknown): BerufDocument | null => {
  if (!validate(raw)) return null;
  return raw as BerufDocument;
};
