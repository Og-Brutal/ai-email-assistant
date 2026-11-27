"use client";

import { useState } from "react";
import type { ParsedEmail } from "@/lib/api";
import { longDate, parseAddress, visibleLabels } from "@/lib/format";
import Attachments from "./Attachments";
import Avatar from "./Avatar";
import EmailHtmlFrame from "./EmailHtmlFrame";
import PlainTextBody from "./PlainTextBody";

/** One email laid out like Gmail: subject, sender row, body, attachments. */
export default function EmailView({ email, myEmail }: { email: ParsedEmail; myEmail: string }) {
  const [showImages, setShowImages] = useState(false);
  const [showQuoted, setShowQuoted] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const sender = parseAddress(email.from);
  const toMe = email.to.length === 1 && parseAddress(email.to[0]).email.toLowerCase() === myEmail.toLowerCase();
  const toText = toMe ? "me" : email.to.map((t) => parseAddress(t).name).join(", ");
  const labels = visibleLabels(email.label_ids);
  const hasQuoted = email.body_html
    ? /gmail_quote|type="cite"/.test(email.body_html)
    : email.body_clean !== email.body_text;

  return (
    <article>
      {/* Subject + label chips */}
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <h1 className="mr-2 text-[22px] font-normal leading-tight">{email.subject || "(no subject)"}</h1>
        {labels.map((l) => (
          <span key={l} className="rounded bg-gray-200 px-1.5 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-300">
            {l}
          </span>
        ))}
      </div>

      {/* Sender row */}
      <div className="mb-4 flex gap-3">
        <Avatar name={sender.name} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4">
            <p className="truncate">
              <span className="font-semibold">{sender.name}</span>{" "}
              {sender.email !== sender.name && (
                <span className="text-sm text-gray-500">&lt;{sender.email}&gt;</span>
              )}
            </p>
            <span className="shrink-0 text-xs text-gray-500">{longDate(email.date)}</span>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            to {toText} {showDetails ? "▴" : "▾"}
          </button>
          {showDetails && (
            <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 rounded-md border border-gray-200 p-3 text-xs dark:border-gray-800">
              <dt className="text-gray-500">from:</dt><dd className="break-all">{email.from}</dd>
              <dt className="text-gray-500">to:</dt><dd className="break-all">{email.to.join(", ")}</dd>
              {email.cc.length > 0 && (<><dt className="text-gray-500">cc:</dt><dd className="break-all">{email.cc.join(", ")}</dd></>)}
              <dt className="text-gray-500">date:</dt><dd>{email.date ? new Date(email.date).toLocaleString() : ""}</dd>
              <dt className="text-gray-500">subject:</dt><dd>{email.subject}</dd>
            </dl>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="sm:pl-[52px]">
        {email.body_html ? (
          <>
            {!showImages && (
              <div className="mb-2 flex items-center justify-between gap-3 rounded-md bg-gray-100 px-3 py-2 text-xs text-gray-600 dark:bg-gray-900 dark:text-gray-400">
                <span>Images are hidden to protect your privacy (they can track when you open emails).</span>
                <button onClick={() => setShowImages(true)} className="shrink-0 font-medium text-blue-500 hover:underline">
                  Show images
                </button>
              </div>
            )}
            <EmailHtmlFrame html={email.body_html} showImages={showImages} showQuoted={showQuoted} />
          </>
        ) : (
          <PlainTextBody text={showQuoted ? email.body_text : email.body_clean || email.body_text} />
        )}

        {hasQuoted && (
          <button
            onClick={() => setShowQuoted(!showQuoted)}
            title={showQuoted ? "Hide trimmed content" : "Show trimmed content"}
            className="mt-2 rounded bg-gray-200 px-2 text-sm leading-5 text-gray-600 hover:bg-gray-300 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
          >
            •••
          </button>
        )}

        <Attachments items={email.attachments} />
      </div>
    </article>
  );
}
