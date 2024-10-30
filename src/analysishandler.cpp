#include "analysishandler.hpp"
#include "analysis.hpp"

#include <iostream>

std::unique_ptr<Analysis> AnalysisHandler::m_analysis(nullptr);

AnalysisHandler::~AnalysisHandler() {}

AnalysisHandler::AnalysisHandler(const Configuration& /*conf*/)
{

  // emptied
}

AnalysisHandler::AnalysisHandler(std::unique_ptr<Analysis>&& ana) { m_analysis.reset(ana.release()); }
