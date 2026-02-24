import { Injectable } from '@nestjs/common';
import { readFile } from 'fs/promises';
import { PDFParse } from 'pdf-parse';

@Injectable()
export class PdfReaderService {
  async extractText(filePath: string): Promise<string> {
    const data = await readFile(filePath);
    const parser = new PDFParse({ data });
    const result = await parser.getText();
    return result.text;
  }
}
