import React, { useState } from 'react';
import { Plan, PlanStep } from '../types';
import { useApp } from '../context/AppContext';
import {
  GripVertical,
  Pencil,
  Check,
  Plus,
  Trash2,
  RotateCcw,
  Sparkles,
  ArrowRight
} from 'lucide-react';

interface PlanApprovalCardProps {
  plan: Plan;
  messageId: string;
}

export const PlanApprovalCard: React.FC<PlanApprovalCardProps> = ({ plan, messageId }) => {
  const {
    approvePlan,
    replanWithFeedback,
    editPlanStep,
    deletePlanStep,
    addPlanStep
  } = useApp();

  const [editingStepId, setEditingStepId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDetail, setEditDetail] = useState('');
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [showAddStep, setShowAddStep] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDetail, setNewDetail] = useState('');

  const isApproved = plan.status === 'approved' || plan.status === 'completed';

  const handleStartEdit = (step: PlanStep) => {
    setEditingStepId(step.id);
    setEditTitle(step.title);
    setEditDetail(step.detail);
  };

  const handleSaveEdit = (stepId: string) => {
    if (editTitle.trim()) {
      editPlanStep(messageId, stepId, editTitle, editDetail);
    }
    setEditingStepId(null);
  };

  const handleCreateStep = () => {
    if (newTitle.trim()) {
      addPlanStep(messageId, newTitle, newDetail);
      setNewTitle('');
      setNewDetail('');
      setShowAddStep(false);
    }
  };

  const handleReplanSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (feedbackText.trim()) {
      replanWithFeedback(messageId, feedbackText);
      setShowFeedbackModal(false);
      setFeedbackText('');
    }
  };

  return (
    <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl p-6 shadow-xl my-4 animate-fade-in relative overflow-hidden">
      {/* Decorative top border accent */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-[#f25c24] via-[#d97706] to-[#f25c24]" />

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-[#1e140f] tracking-tight flex items-center gap-2">
            <span>Plan ready — your call</span>
            {isApproved && (
              <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full border border-emerald-300">
                Approved
              </span>
            )}
          </h3>
          <p className="text-sm text-[#786558] italic mt-0.5">
            Edit, reorder or approve. Nothing runs until you say so.
          </p>
        </div>
      </div>

      {/* Step List */}
      <div className="space-y-2.5 my-5">
        {plan.steps.map((step, index) => {
          const isEditing = editingStepId === step.id;

          return (
            <div
              key={step.id}
              className={`bg-[#f7f2ea] border border-[#e4d9c7] rounded-2xl p-3.5 flex items-center justify-between gap-3 transition-all ${
                isApproved ? 'opacity-85' : 'hover:border-[#cbb8a3]'
              }`}
            >
              {/* Drag Handle & Number badge */}
              <div className="flex items-center gap-3 shrink-0">
                {!isApproved && (
                  <GripVertical className="w-4 h-4 text-[#a89586] cursor-grab hover:text-[#1e140f]" />
                )}
                <div className="w-7 h-7 rounded-full bg-[#f25c24] text-white font-bold flex items-center justify-center text-xs shadow-sm shadow-[#f25c24]/30">
                  {index + 1}
                </div>
              </div>

              {/* Content / Edit form */}
              <div className="flex-1 min-w-0">
                {isEditing ? (
                  <div className="space-y-1.5">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={e => setEditTitle(e.target.value)}
                      className="w-full text-xs font-semibold px-2 py-1 rounded border border-[#bfaaa0] bg-white text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                      placeholder="Step title"
                    />
                    <input
                      type="text"
                      value={editDetail}
                      onChange={e => setEditDetail(e.target.value)}
                      className="w-full text-xs px-2 py-1 rounded border border-[#bfaaa0] bg-white text-[#6b584d] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                      placeholder="Step detail / duration"
                    />
                  </div>
                ) : (
                  <div>
                    <div className="font-bold text-sm text-[#1e140f]">{step.title}</div>
                    <div className="text-xs text-[#725e51]">{step.detail}</div>
                  </div>
                )}
              </div>

              {/* Edit / Save / Delete actions */}
              {!isApproved && (
                <div className="flex items-center gap-1 shrink-0">
                  {isEditing ? (
                    <button
                      onClick={() => handleSaveEdit(step.id)}
                      className="p-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                      title="Save step"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleStartEdit(step)}
                        className="p-1.5 rounded-lg hover:bg-[#eadecc] text-[#786558] hover:text-[#1e140f] transition-colors"
                        title="Edit step"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      {plan.steps.length > 1 && (
                        <button
                          onClick={() => deletePlanStep(messageId, step.id)}
                          className="p-1.5 rounded-lg hover:bg-red-100 text-[#786558] hover:text-red-600 transition-colors"
                          title="Delete step"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Add Step input */}
        {!isApproved && (
          <div>
            {showAddStep ? (
              <div className="bg-[#f2ece2] border border-[#d8cbb8] rounded-2xl p-3 space-y-2">
                <input
                  type="text"
                  placeholder="New step title"
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  className="w-full text-xs font-medium px-3 py-1.5 rounded-lg bg-white border border-[#cbb8a3] text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                />
                <input
                  type="text"
                  placeholder="Detail / timeline (e.g., weeks 10-12)"
                  value={newDetail}
                  onChange={e => setNewDetail(e.target.value)}
                  className="w-full text-xs px-3 py-1.5 rounded-lg bg-white border border-[#cbb8a3] text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                />
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={handleCreateStep}
                    className="text-xs bg-[#f25c24] text-white font-medium px-3 py-1 rounded-lg hover:bg-[#d94c17]"
                  >
                    Add step
                  </button>
                  <button
                    onClick={() => setShowAddStep(false)}
                    className="text-xs text-[#786558] hover:text-[#1e140f] px-2 py-1"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowAddStep(true)}
                className="w-full py-2 border border-dashed border-[#cbb8a3] hover:border-[#f25c24] rounded-2xl text-xs font-medium text-[#786558] hover:text-[#f25c24] flex items-center justify-center gap-1.5 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add step to plan</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Main Action Bar */}
      {!isApproved ? (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#e6decb]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => approvePlan(messageId)}
              className="bg-[#f25c24] hover:bg-[#d94c17] text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-md shadow-[#f25c24]/20 flex items-center gap-2 transition-all hover:scale-[1.02] active:scale-100"
            >
              <span>Approve plan</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => setShowFeedbackModal(true)}
              className="bg-transparent hover:bg-[#f1ebd8] border-1.5 border-[#cbb8a3] text-[#1e140f] font-semibold text-sm px-4 py-2.5 rounded-xl transition-colors flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5 text-[#786558]" />
              <span>Re-plan with feedback</span>
            </button>
          </div>

          <button
            onClick={() => approvePlan(messageId)}
            className="text-xs text-[#786558] hover:text-[#1e140f] italic hover:underline font-medium"
          >
            Approve & don't ask again
          </button>
        </div>
      ) : (
        <div className="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-xl flex items-center gap-2 font-medium">
          <Check className="w-4 h-4 text-emerald-600" />
          <span>Plan approved by user. Retrieval and reasoning completed based on this sequence.</span>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedbackModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl p-6 max-w-md w-full shadow-2xl animate-fade-in">
            <h4 className="text-lg font-bold text-[#1e140f] mb-1">Re-plan with feedback</h4>
            <p className="text-xs text-[#786558] mb-4">
              Tell the Planner what to modify (e.g. adjust week timeline, add Spring Boot, focus more on DP).
            </p>
            <form onSubmit={handleReplanSubmit} className="space-y-4">
              <textarea
                value={feedbackText}
                onChange={e => setFeedbackText(e.target.value)}
                rows={3}
                placeholder="Enter your instructions for re-planning..."
                className="w-full text-xs p-3 rounded-xl border border-[#cbb8a3] bg-white text-[#1e140f] focus:outline-none focus:ring-2 focus:ring-[#f25c24]"
                autoFocus
              />
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowFeedbackModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-[#786558] hover:text-[#1e140f]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-xs font-semibold bg-[#f25c24] text-white rounded-xl hover:bg-[#d94c17]"
                >
                  Generate revised plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
