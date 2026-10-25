import React, { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown, Send, X } from 'lucide-react';
import { FeedbackService } from '../lib/api';

interface FeedbackButtonsProps {
  messageId: string;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({ messageId }) => {
  const [rating, setRating] = useState<number>(0);
  const [comment, setComment] = useState<string>('');
  const [showPopover, setShowPopover] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    FeedbackService.get(messageId)
      .then(res => {
        if (mounted && res) {
          setRating(res.rating || 0);
          setComment(res.comment || '');
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, [messageId]);

  const handleVote = async (newRating: number) => {
    const nextRating = rating === newRating ? 0 : newRating;
    setRating(nextRating);

    if (nextRating === -1) {
      setShowPopover(true);
    } else {
      setShowPopover(false);
      try {
        await FeedbackService.submit(messageId, nextRating);
      } catch (e) {
        console.error('Failed to submit feedback:', e);
      }
    }
  };

  const handleCommentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await FeedbackService.submit(messageId, -1, comment);
      setShowPopover(false);
    } catch (e) {
      console.error('Failed to submit feedback with comment:', e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative inline-flex items-center gap-1.5">
      <button
        onClick={() => handleVote(1)}
        className={`p-1 rounded transition-colors ${
          rating === 1
            ? 'text-emerald-400 bg-emerald-500/10'
            : 'text-[#8e7869] hover:text-emerald-400'
        }`}
        title="Helpful (+1)"
      >
        <ThumbsUp className="w-3.5 h-3.5" />
      </button>

      <button
        onClick={() => handleVote(-1)}
        className={`p-1 rounded transition-colors ${
          rating === -1
            ? 'text-red-400 bg-red-500/10'
            : 'text-[#8e7869] hover:text-red-400'
        }`}
        title="Not helpful (-1)"
      >
        <ThumbsDown className="w-3.5 h-3.5" />
      </button>

      {/* Thumbs Down Comment Popover */}
      {showPopover && (
        <div className="absolute right-0 bottom-full mb-2 w-64 bg-[#1e140d] border border-[#443024] rounded-xl p-3 shadow-2xl z-30 animate-fade-in text-xs space-y-2">
          <div className="flex items-center justify-between text-[#d6c9bd] font-medium">
            <span>What could be improved?</span>
            <button
              onClick={() => setShowPopover(false)}
              className="text-[#8e7869] hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <form onSubmit={handleCommentSubmit} className="space-y-2">
            <textarea
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="Explain what was inaccurate or unhelpful (max 500 chars)..."
              maxLength={500}
              rows={3}
              className="w-full bg-[#140c07] border border-[#3b271d] rounded-lg p-2 text-[#fbf8f2] placeholder-[#796659] text-xs focus:outline-none focus:border-[#f25c24]"
            />
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#796659]">{comment.length}/500</span>
              <button
                type="submit"
                disabled={isSubmitting}
                className="bg-[#f25c24] hover:bg-[#d94c17] text-white px-2.5 py-1 rounded-md text-[11px] font-medium flex items-center gap-1 transition-colors"
              >
                <Send className="w-3 h-3" />
                <span>Submit</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
