#include "postprocessing.hpp"

#include <iostream>

#include "TString.h"

using namespace std;

std::unique_ptr<PostProcessingTool> PostProcessingTool::the_instance(nullptr);

PostProcessingTool::PostProcessingTool(const Configuration& conf) : m_config(conf) {}

void PostProcessingTool::createInstance(const Configuration& conf)
{
  if( !the_instance ) {
    cout << "INFO:    PostProcessingTool::createInstance() PostProcessingTool pointer is NULL." << endl;
    cout << "         Will instanciate the PostProcessingTool service first." << endl;
    the_instance.reset(new PostProcessingTool(conf));
  }
}

PostProcessingTool& PostProcessingTool::getInstance()
{
  if( the_instance == nullptr ) {
    cout << "ERROR:    PostProcessingTool::getInstance() PostProcessingTool pointer is NULL." << endl;
    cout << "          It should be initialized with a Configuration first." << endl;
    throw;
  }
  return *the_instance;
}

void PostProcessingTool::process(const TString& wsfilename)
{
  // do nothing by default
}
