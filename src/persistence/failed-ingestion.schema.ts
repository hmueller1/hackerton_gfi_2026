import { Document, Schema } from 'mongoose';

export const FAILED_INGESTIONS_COLLECTION = 'failed_ingestions';

export type FailedIngestionDocument = Document & {
  filename: string;
  reason: string;
  retryCount: number;
  lastAttemptAt: Date;
};

export const FailedIngestionSchemaDefinition = new Schema<FailedIngestionDocument>(
  {
    filename: { type: String, required: true, unique: true },
    reason: { type: String, required: true },
    retryCount: { type: Number, required: true },
    lastAttemptAt: { type: Date, required: true },
  },
  { timestamps: true },
);
