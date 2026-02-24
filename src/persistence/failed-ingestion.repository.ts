import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  FAILED_INGESTIONS_COLLECTION,
  FailedIngestionDocument,
} from './failed-ingestion.schema';

@Injectable()
export class FailedIngestionRepository {
  constructor(
    @InjectModel(FAILED_INGESTIONS_COLLECTION)
    private readonly model: Model<FailedIngestionDocument>,
  ) {}

  async upsert(filename: string, reason: string, retryCount: number): Promise<void> {
    await this.model.findOneAndUpdate(
      { filename },
      { reason, retryCount, lastAttemptAt: new Date() },
      { upsert: true },
    );
  }

  async deleteByFilename(filename: string): Promise<void> {
    await this.model.deleteOne({ filename });
  }

  async findAll(): Promise<FailedIngestionDocument[]> {
    return this.model.find().exec();
  }
}
