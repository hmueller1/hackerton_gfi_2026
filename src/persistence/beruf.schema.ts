import { Document, Schema } from 'mongoose';
import { BerufDocument } from '../domain/interfaces';

export const BERUFE_COLLECTION = 'berufe';

export type BerufeDocument = BerufDocument & Document & { filename: string };

const TerminSchema = new Schema(
  {
    datum: { type: String, required: false },
    uhrzeitvon: { type: String, required: false },
    uhrzeitbis: { type: String, required: false },
    dauer: { type: Number, required: true },
  },
  { _id: false },
);

const AufgabeSchema = new Schema(
  {
    name: { type: String, required: true },
    struktur: { type: String, required: true },
    termin: { type: TerminSchema, required: true },
    hilfmittel: { type: String, required: false },
  },
  { _id: false },
);

const PruefungsBereichSchema = new Schema(
  {
    name: { type: String, required: true },
    aufgaben: { type: [AufgabeSchema], required: true },
  },
  { _id: false },
);

export const BerufSchemaDefinition = new Schema<BerufeDocument>(
  {
    filename: { type: String, required: true, unique: true },
    beruf: {
      beschreibung: { type: String, required: true },
      berufNr: { type: [Number], required: true },
      pruefungsBereiche: { type: [PruefungsBereichSchema], required: true },
    },
  },
  { timestamps: true },
);
