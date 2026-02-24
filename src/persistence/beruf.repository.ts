import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { BerufDocument } from '../domain/interfaces';
import { BERUFE_COLLECTION, BerufeDocument } from './beruf.schema';

@Injectable()
export class BerufRepository {
  constructor(
    @InjectModel(BERUFE_COLLECTION)
    private readonly model: Model<BerufeDocument>,
  ) {}

  async existsByFilename(filename: string): Promise<boolean> {
    const count = await this.model.countDocuments({ filename }).exec();
    return count > 0;
  }

  async save(filename: string, doc: BerufDocument): Promise<void> {
    await this.model.create({ filename, beruf: doc.beruf });
  }
}
