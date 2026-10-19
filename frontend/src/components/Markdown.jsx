import { marked } from "marked";
import DOMPurify from "dompurify";

export default function Markdown({ text }) {
  const html = DOMPurify.sanitize(marked.parse(String(text || "")));
  return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />;
}